from celery import Celery

app = Celery('awesome_isp_celery',
             backend='rpc://',
             include=['awesome_isp_celery.tasks'])
