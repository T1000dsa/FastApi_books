from celery import Celery
from src.core.config.config import settings

celery_app = Celery(
    "worker",
    broker=f"redis://{settings.redis_settings.host}:{settings.redis_settings.port}/{settings.redis_settings.db}",
    backend=f"redis://{settings.redis_settings.host}:{settings.redis_settings.port}/{settings.redis_settings.db}",
    include=["src.core.services.task_queue.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_ignore_result=False,
    task_routes={
        "src.core.services.task_queue.tasks.*": {"queue": "main-queue"}
    },
    beat_schedule={
        'cleanup-expired-tokens': {
            'task': 'src.core.services.task_queue.tasks.cleanup_expired_tokens',
            'schedule': 3600.0,  # Every hour
        },
    }
)