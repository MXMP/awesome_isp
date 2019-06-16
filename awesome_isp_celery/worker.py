import os

from celery import Celery

app = Celery(backend='rpc://',
             include=['tasks'])

app.conf.beat_schedule = {
    'refresh': {
        'task': 'discover_hosts',
        'schedule': float(os.environ['SCHEDULE_TIME']),
        'args': (os.environ['NETWORKS_TO_DISCOVER'].split(','),),
    },
}
