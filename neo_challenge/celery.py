import os
from celery import Celery
from prometheus_client import start_http_server, multiprocess, CollectorRegistry
import threading
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_challenge.settings')

logger = logging.getLogger(__name__)

app = Celery('neo_challenge')
app.config_from_object('django.conf:settings', namespace='CELERY')

def start_metrics_server():
    try:
        logger.info("Starting Prometheus metrics server on port 8001")
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        start_http_server(8001, addr='0.0.0.0', registry=registry)
        logger.info("Prometheus metrics server started successfully")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")

# Start metrics server immediately
thread = threading.Thread(target=start_metrics_server, daemon=True)
thread.start()

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')