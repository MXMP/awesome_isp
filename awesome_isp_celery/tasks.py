import os
import subprocess
from ipaddress import ip_network

from pymongo import MongoClient
from easysnmp import Session
from celery.utils.log import get_task_logger

from worker import app

logger = get_task_logger(__name__)

# Cписок моделей
models = ['DES-3200-28/C1',
          'DGS-3100-24TG',
          'DGS-1510-28L/ME']


@app.task(bind=True, name='discover_hosts')
def discover_hosts(self, networks):
    for net in networks:
        network = ip_network(net)
        hosts = network.hosts()
        for host in hosts:
            check_host.s(host.compressed).delay()


@app.task(bind=True, name='check_host')
def check_host(self, hostname):
    logger.info(f'Check host: {hostname}')
    session = Session(hostname=hostname, community=os.environ['READ_COMMUNITY'], version=2)
    sys_descr = session.get('.1.3.6.1.2.1.1.1.0')
    logger.info(f'sysDescr: {sys_descr}')
    for model in models:
        if model in sys_descr.value:
            save_host.s(hostname, model, 'ok', {}).delay()
            return

    sys_name = session.get('.1.3.6.1.2.1.1.5.0')
    logger.info(f'sysName: {sys_name}')
    for model in models:
        if model in sys_name.value:
            save_host.s(hostname, model, 'ok', {}).delay()
            return


@app.task(bind=True, name='ping_host')
def ping_host(self, hostname):
    return subprocess.run(['ping', '-q', '-c', '1', hostname]).returncode


@app.task(bind=True, name='save_host')
def save_host(self, ip_address, model, status, lldp_info):
    mongo = MongoClient(os.environ['MONGO_HOST'])
    db = mongo.awesome_isp
    hosts = db.hosts
    hosts.find_one_and_update({'ip': ip_address},
                              {'$set': {'status': status,
                                        'model': model,
                                        'lldp_info': lldp_info}},
                              upsert=True)
