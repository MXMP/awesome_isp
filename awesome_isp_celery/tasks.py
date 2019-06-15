import time
import subprocess

from pymongo import MongoClient
from easysnmp import Session

from awesome_isp_celery.celery import app


# Cписок моделей
models = ['DES-3200-28/C1',
          'DGS-3100-24TG',
          'DGS-1510-28L/ME']


@app.task
def ping_host(hostname):
    return subprocess.run(['ping', '-q', '-c', '1', hostname]).returncode


@app.task
def get_model(ip_address):
    session = Session(hostname=ip_address, community='readonly', version=2)
    sys_descr = session.get('.1.3.6.1.2.1.1.1.0')
    for model in models:
        if model in sys_descr:
            return model

    sys_name = session.get('.1.3.6.1.2.1.1.5.0')
    for model in models:
        if model in sys_name:
            return model


@app.task(bind=True, name='save_host')
def save_host(ip_address, model, status, lldp_info):
    mongo = MongoClient('mongodb://localhost:27017')
    hosts = mongo.awesome_isp_hosts
    host = {"ip": ip_address,
            "model": model,
            "status": status,
            "lldp_info": lldp_info}
    host_id = hosts.insert_one(host).inserted_id
    return host_id
