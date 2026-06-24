"""Periodic iTop CMDB sync task."""

from app.core.scheduler.celery_app import celery_app


@celery_app.task(
    name="asset.sync_from_itop",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sync_from_itop(self):
    # TODO: Implement iTop adapter sync logic
    return {"message": "iTop sync not yet implemented", "status": "skipped"}
