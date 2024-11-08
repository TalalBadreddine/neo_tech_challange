import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_challenge.settings')

BROKER_URL = os.getenv('CELERY_BROKER_URL')
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', BROKER_URL)

app = Celery('neo_challenge')

app.conf.update(
    broker_url=BROKER_URL,
    result_backend=RESULT_BACKEND,
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
)

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')