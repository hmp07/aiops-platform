"""M11 Scheduler — API for task, adapter and datasource management."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.core.scheduler.celery_app import celery_app
from app.modules.module11_scheduler.repository import DataSourceRepository
from app.modules.module11_scheduler.service import DataSourceService

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])
ds_router = APIRouter(prefix="/datasources", tags=["Data Sources"])

def _get_ds_svc(db: AsyncSession = Depends(get_db)) -> DataSourceService:
    return DataSourceService(DataSourceRepository(db))


@router.get("/tasks")
async def list_tasks(current_user: dict = Depends(get_current_user)):
    """List registered Celery tasks."""
    tasks = []
    for name in celery_app.tasks:
        if not name.startswith("celery."):
            task = celery_app.tasks[name]
            tasks.append({"name": name, "routing_key": task.routing_key or ""})
    return {"total": len(tasks), "items": tasks}


@router.get("/tasks/{task_name}")
async def get_task(task_name: str, current_user: dict = Depends(get_current_user)):
    """Get task details and status."""
    task = celery_app.tasks.get(task_name)
    if not task:
        return {"error": "Task not found"}
    info = {"name": task_name, "max_retries": task.max_retries,
            "default_retry_delay": task.default_retry_delay,
            "acks_late": task.acks_late}
    return info


@router.post("/tasks/{task_name}/run")
@require_permission("platform:task:manage")
async def run_task(task_name: str, current_user: dict = Depends(get_current_user)):
    """Trigger a task immediately."""
    result = celery_app.send_task(task_name)
    return {"task_id": result.id, "status": "dispatched"}


@router.get("/adapters/health")
async def adapter_health(current_user: dict = Depends(get_current_user)):
    """Check health of all integration adapters."""
    adapters = {}
    # Check database
    try:
        from app.core.database.session import async_session_factory
        async with async_session_factory() as db:
            await db.execute(db.execute.__func__)
        adapters["database"] = "healthy"
    except Exception:
        adapters["database"] = "unhealthy"
    # Check Redis
    try:
        from app.core.cache.redis import get_redis
        r = await get_redis()
        await r.ping()
        adapters["redis"] = "healthy"
    except Exception:
        adapters["redis"] = "unhealthy"
    return {"adapters": adapters}


# ---- Data Sources ----
@ds_router.get("/types")
async def list_source_types(current_user: dict = Depends(get_current_user)):
    from app.integrations.registry import list_types
    return {"items": list_types()}

@ds_router.get("")
async def list_datasources(current_user: dict = Depends(get_current_user),
                           svc: DataSourceService = Depends(_get_ds_svc)):
    items = await svc.list_all()
    return {"total": len(items), "items": items}

@ds_router.post("", status_code=201)
@require_permission("platform:task:manage")
async def create_datasource(body: dict, current_user: dict = Depends(get_current_user),
                            svc: DataSourceService = Depends(_get_ds_svc)):
    return await svc.create(body)

@ds_router.get("/{ds_id}")
async def get_datasource(ds_id: UUID, current_user: dict = Depends(get_current_user),
                         svc: DataSourceService = Depends(_get_ds_svc)):
    return await svc.get(ds_id)

@ds_router.post("/{ds_id}/update")
@require_permission("platform:task:manage")
async def update_datasource(ds_id: UUID, body: dict, current_user: dict = Depends(get_current_user),
                            svc: DataSourceService = Depends(_get_ds_svc)):
    return await svc.update(ds_id, body)

@ds_router.post("/{ds_id}/delete")
@require_permission("platform:task:manage")
async def delete_datasource(ds_id: UUID, current_user: dict = Depends(get_current_user),
                            svc: DataSourceService = Depends(_get_ds_svc)):
    await svc.delete(ds_id)
    return {"status": "deleted"}

@ds_router.post("/{ds_id}/test")
async def test_datasource(ds_id: UUID, current_user: dict = Depends(get_current_user),
                          svc: DataSourceService = Depends(_get_ds_svc)):
    result = await svc.test_connection(ds_id)
    return result

@ds_router.post("/{ds_id}/sync")
@require_permission("platform:task:manage")
async def sync_datasource(ds_id: UUID, current_user: dict = Depends(get_current_user),
                          svc: DataSourceService = Depends(_get_ds_svc)):
    result = await svc.sync(ds_id)
    return result
