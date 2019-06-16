import os

from celery import Celery

app = Celery('awesome_isp_celery',
             backend='rpc://',
             include=['awesome_isp_celery.tasks'])

app.conf.beat_schedule = {
    'refresh': {
        'task': 'discover_hosts',
        'schedule': float(os.environ['SCHEDULE_TIME']),
        'args': (os.environ['NETWORKS_TO_DISCOVER'].split(','),),
    },
}
