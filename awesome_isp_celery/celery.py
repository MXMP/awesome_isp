from celery import Celery

app = Celery('awesome_isp_celery',
             broker='amqp://guest:guest@localhost/',
             backend='rpc://',
             include=['awesome_isp_celery.tasks'])
