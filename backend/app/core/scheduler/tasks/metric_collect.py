"""Periodic metric collection task."""

from app.core.scheduler.celery_app import celery_app


@celery_app.task(
    name="monitoring.collect_metrics",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def collect_metrics(self):
    # TODO: Implement Zabbix/SNMP metric collection
    return {"message": "Metric collection not yet implemented", "status": "skipped"}
