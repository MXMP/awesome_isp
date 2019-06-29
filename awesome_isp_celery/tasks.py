import os
import subprocess
import json
from ipaddress import ip_network

from pymongo import MongoClient
from easysnmp import Session, EasySNMPTimeoutError
from celery.utils.log import get_task_logger

from worker import app

logger = get_task_logger(__name__)

# Cписок моделей
models = ['DES-3200-28/C1',
          'DGS-3100-24TG',
          'DGS-1510-28L/ME']


def mac_bin_to_hex(inc_bin_mac_address):
    octets = [ord(c) for c in inc_bin_mac_address]
    return "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(*octets)


@app.task(bind=True, name='discover_hosts')
def discover_hosts(self, networks):
    for net in networks:
        network = ip_network(net)
        hosts = network.hosts()
        for host in hosts:
            check_host.s(host.compressed).delay()


@app.task(bind=True, name='discover_nbrs')
def discover_nbrs(self):
    mongo = MongoClient(os.environ['MONGO_HOST'], connect=False)
    db = mongo.awesome_isp
    hosts = db.hosts
    for host in hosts.find():
        get_lldp_info.s(host['id'], host['ip']).delay()
    mongo.close()


@app.task(bind=True, name='check_host')
def check_host(self, hostname):
    logger.info(f'Check host: {hostname}')
    session = Session(hostname=hostname, community=os.environ['READ_COMMUNITY'], version=2)
    try:
        local_chassis_id = session.get('.1.0.8802.1.1.2.1.3.2.0')
    except EasySNMPTimeoutError:
        logger.info(f'Host {hostname} is down.')
    else:
        chassis_id = mac_bin_to_hex(local_chassis_id.value)
        save_host.s(chassis_id, ip=hostname).delay()
        check_model.s(chassis_id, hostname).delay()


@app.task(bind=True, name='check_model')
def check_model(self, id, hostname):
    logger.info(f'Check model: {hostname}')
    session = Session(hostname=hostname, community=os.environ['READ_COMMUNITY'], version=2)
    sys_descr = session.get('.1.3.6.1.2.1.1.1.0')
    logger.info(f'sysDescr: {sys_descr}')
    for model in models:
        if model in sys_descr.value:
            save_host.s(id, model=model).delay()
            return

    sys_name = session.get('.1.3.6.1.2.1.1.5.0')
    logger.info(f'sysName: {sys_name}')
    for model in models:
        if model in sys_name.value:
            save_host.s(id, model=model).delay()
            return


@app.task(bind=True, name='get_lldp_info')
def get_lldp_info(self, id, hostname):
    logger.info(f'Getting LLDP for host: {hostname}')
    session = Session(hostname=hostname, community=os.environ['READ_COMMUNITY'], version=2)
    try:
        nbr_mac_addresses = session.walk('.1.0.8802.1.1.2.1.4.1.1.5')
    except EasySNMPTimeoutError:
        save_host.s(id, status='down').delay()
    else:
        nbrs = []
        for entry in nbr_mac_addresses:
            try:
                nbrs.append(mac_bin_to_hex(entry.value))
            except IndexError:
                logger.error(f'Error while convert MAC: {entry.value}')
                continue
        save_host.s(id, lldp_nbrs=nbrs).delay()


@app.task(bind=True, name='save_host')
def save_host(self, id, **kwargs):
    mongo = MongoClient(os.environ['MONGO_HOST'], connect=False)
    db = mongo.awesome_isp
    hosts = db.hosts
    on_insert = {'status': 'ok',
                 'lldp_nbrs': [],
                 'model': 'unknown'}
    for key in kwargs:
        if key in on_insert:
            on_insert.pop(key)
    hosts.find_one_and_update({'id': id},
                              {'$set': kwargs,
                               '$setOnInsert': on_insert,
                               '$currentDate': {'last_check': True}},
                              upsert=True)
    mongo.close()


@app.task(bind=True, name='make_json')
def make_json(self):
    mongo = MongoClient(os.environ['MONGO_HOST'], connect=False)
    db = mongo.awesome_isp
    hosts = db.hosts
    nodes = []
    links = []
    for host in hosts.find():
        nodes.append({"id": host['id'],
                      "ip": host['ip'],
                      "model": host['model'],
                      "status": host['status'],
                      "group": "switches",
                      "radius": 2})
        for nbr in host['lldp_nbrs']:
            if hosts.find({'id': nbr}).count() != 0:
                links.append({'source': host['id'],
                              'target': nbr,
                              'value': 2})
    mongo.close()
    with open("/usr/share/nginx/html/graph.json", "w") as graph_file:
        json.dump({"nodes": nodes, "links": links}, graph_file)
