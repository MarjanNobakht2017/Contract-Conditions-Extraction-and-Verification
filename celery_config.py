from celery import Celery
import os

redis_url = os.getenv('REDIS_URL')

celery_app = Celery('app', broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_routes={
        'app.process_files': {'queue': 'process_files'},
    },
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
)

import app