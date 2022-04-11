from celery import Celery


app = Celery('accounts')

app.config_from_object('django.conf:settings', namespace='CELERY')
