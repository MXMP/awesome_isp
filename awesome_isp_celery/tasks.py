import time
import subprocess

from awesome_isp_celery.celery import app


@app.task
def longtime_add(x, y):
    print('[tasks] long time task begins')
    # sleep 5 seconds
    time.sleep(5)
    print('[tasks] long time task finished')
    return x + y


@app.task
def ping_host(hostname):
    return subprocess.run(['ping', '-q', '-c', '1', hostname]).returncode
