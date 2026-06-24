"""Periodic configuration backup task."""

from app.core.scheduler.celery_app import celery_app


@celery_app.task(
    name="config.backup_all",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def backup_all_configs(self):
    # TODO: Implement SSH/Netmiko config backup
    return {"message": "Config backup not yet implemented", "status": "skipped"}
