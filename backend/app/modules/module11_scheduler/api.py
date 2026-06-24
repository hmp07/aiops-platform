"""M11 Scheduler — API for task and adapter management."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.core.scheduler.celery_app import celery_app

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


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
    except Exception as e:
        adapters["database"] = f"unhealthy: {e}"
    # Check Redis
    try:
        from app.core.cache.redis import get_redis
        r = await get_redis()
        await r.ping()
        adapters["redis"] = "healthy"
    except Exception as e:
        adapters["redis"] = f"unhealthy: {e}"
    return {"adapters": adapters}
