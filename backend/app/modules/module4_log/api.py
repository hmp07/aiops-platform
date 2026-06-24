"""M4 Log Analysis — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module4_log.repository import LogRepository, LogSourceRepository
from app.modules.module4_log.schemas import (
    LogIngestRequest, LogListResponse, LogSourceCreate, LogSourceResponse,
)

router = APIRouter(prefix="/logs", tags=["Log Analysis"])

def _get_log_repo(db: AsyncSession = Depends(get_db)) -> LogRepository:
    return LogRepository(db)

def _get_src_repo(db: AsyncSession = Depends(get_db)) -> LogSourceRepository:
    return LogSourceRepository(db)


@router.get("/entries", response_model=LogListResponse)
async def list_logs(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    device_id: UUID | None = None, severity: str | None = None,
    source: str | None = None, keyword: str | None = None,
    current_user: dict = Depends(get_current_user), repo: LogRepository = Depends(_get_log_repo)):
    total, items = await repo.list_all(page, page_size, device_id, severity, source, keyword)
    return LogListResponse(total=total, items=[{
        "id": r.id, "time": r.time, "device_id": r.device_id, "source": r.source,
        "facility": r.facility, "severity": r.severity, "hostname": r.hostname,
        "message": r.message, "parsed_fields": r.parsed_fields,
    } for r in items])

@router.post("/ingest", status_code=201)
@require_permission("log:entry:search")
async def ingest_logs(req: LogIngestRequest, current_user: dict = Depends(get_current_user),
                      repo: LogRepository = Depends(_get_log_repo)):
    count = 0
    for msg in req.messages[:100]:
        await repo.create({"message": msg.get("message", ""), "severity": msg.get("severity", "info"),
                           "source": req.source, "hostname": msg.get("hostname"),
                           "device_id": msg.get("device_id"), "facility": msg.get("facility")})
        count += 1
    return {"ingested": count}

@router.get("/sources", response_model=list[LogSourceResponse])
async def list_sources(current_user: dict = Depends(get_current_user),
                       repo: LogSourceRepository = Depends(_get_src_repo)):
    sources = await repo.list_all()
    return [{"id": s.id, "name": s.name, "source_type": s.source_type,
             "host": s.host, "config": {k:v for k,v in s.config.items()
             if k not in ("password","token","secret")}, "is_enabled": s.is_enabled,
             "created_at": s.created_at} for s in sources]

@router.post("/sources", response_model=LogSourceResponse, status_code=201)
@require_permission("log:source:create")
async def create_source(req: LogSourceCreate, current_user: dict = Depends(get_current_user),
                        repo: LogSourceRepository = Depends(_get_src_repo)):
    obj = await repo.create(req.model_dump())
    return {"id": obj.id, "name": obj.name, "source_type": obj.source_type,
            "host": obj.host, "config": {}, "is_enabled": obj.is_enabled, "created_at": obj.created_at}
