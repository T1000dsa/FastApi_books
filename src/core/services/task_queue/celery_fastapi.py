from celery import Celery

from src.core.config.config import settings


celery_app = Celery(
    "worker",
    broker=f"redis://{settings.redis_settings.host}:{settings.redis_settings.port}/{settings.redis_settings.db}",
    backend=f"redis://{settings.redis_settings.host}:{settings.redis_settings.port}/{settings.redis_settings.db}"
)

# Configure Celery with additional settings
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    # Use the same Redis settings for result backend
    result_backend=f"redis://{settings.redis_settings.host}:{settings.redis_settings.port}/{settings.redis_settings.db}",
    # Optional: Configure task routes if needed
    task_routes={
        "app.tasks.*": {"queue": "main-queue"}
    }
)
