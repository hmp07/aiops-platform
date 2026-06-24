"""M5 Config — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module5_config.repository import BackupRepository, BatchRepository, DiffRepository
from app.modules.module5_config.schemas import (
    BackupListResponse, BackupTriggerRequest, DiffListResponse,
)
from app.modules.module5_config.service import ConfigBackupService, ConfigDiffService

router = APIRouter(prefix="/configs", tags=["Config Management"])


def _get_backup_svc(db: AsyncSession = Depends(get_db)) -> ConfigBackupService:
    return ConfigBackupService(BackupRepository(db))


def _get_diff_svc(db: AsyncSession = Depends(get_db)) -> ConfigDiffService:
    return ConfigDiffService(DiffRepository(db), BackupRepository(db))


@router.get("/backups", response_model=BackupListResponse)
async def list_backups(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    device_id: UUID | None = None, status: str | None = None,
    _: dict = Depends(get_current_user),
    svc: ConfigBackupService = Depends(_get_backup_svc),
):
    total, items = await svc.list_backups(page, page_size, device_id, status)
    return BackupListResponse(total=total, items=items)


@router.post("/backups/trigger")
@require_permission("config:backup:trigger")
async def trigger_backup(
    req: BackupTriggerRequest = BackupTriggerRequest(),
    _u: dict = Depends(get_current_user),
    svc: ConfigBackupService = Depends(_get_backup_svc),
):
    items = await svc.trigger_backup(req.device_ids)
    return {"backups_created": len(items), "items": items}


@router.get("/diff/{device_id}")
async def get_diff(
    device_id: UUID,
    _: dict = Depends(get_current_user),
    svc: ConfigDiffService = Depends(_get_diff_svc),
):
    return await svc.get_diff(device_id)


@router.get("/diffs", response_model=DiffListResponse)
async def list_diffs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    device_id: UUID | None = None,
    _: dict = Depends(get_current_user),
    svc: ConfigDiffService = Depends(_get_diff_svc),
):
    total, items = await svc.list_diffs(page, page_size, device_id)
    return DiffListResponse(total=total, items=items)
