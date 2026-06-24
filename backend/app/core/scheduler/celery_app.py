from celery import Celery

from app.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "aiops",
    broker=settings.REDIS_CELERY_BROKER_URL,
    backend=settings.REDIS_CELERY_RESULT_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_soft_time_limit=600,
    task_time_limit=900,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    imports=(
        "app.core.scheduler.tasks.asset_sync",
        "app.core.scheduler.tasks.metric_collect",
        "app.core.scheduler.tasks.config_backup",
        "app.core.scheduler.tasks.inspection",
    ),
)
