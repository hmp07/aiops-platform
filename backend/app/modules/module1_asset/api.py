"""M1 Asset — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module1_asset.repository import CalibrationRepository, DeviceRepository
from app.modules.module1_asset.schemas import (
    CalibrationApproveRequest, CalibrationListResponse, CalibrationRunRequest,
    DeviceCreate, DeviceListResponse, DeviceResponse, DeviceUpdate,
)
from app.modules.module1_asset.service import CalibrationService, DeviceManageService, DeviceQueryService

router = APIRouter(prefix="/devices", tags=["Asset Management"])
cal_router = APIRouter(prefix="/calibrations", tags=["Asset Calibration"])


def _get_query_svc(db: AsyncSession = Depends(get_db)) -> DeviceQueryService:
    return DeviceQueryService(DeviceRepository(db))


def _get_manage_svc(db: AsyncSession = Depends(get_db)) -> DeviceManageService:
    repo = DeviceRepository(db)
    return DeviceManageService(repo, DeviceQueryService(repo))


def _get_cal_svc(db: AsyncSession = Depends(get_db)) -> CalibrationService:
    return CalibrationService(CalibrationRepository(db), DeviceRepository(db))


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    device_type: str | None = None, vendor: str | None = None,
    lifecycle_status: str | None = None, keyword: str | None = None,
    _: dict = Depends(get_current_user),
    svc: DeviceQueryService = Depends(_get_query_svc),
):
    total, items = await svc.list_devices(page, page_size, device_type, vendor, lifecycle_status, keyword)
    return DeviceListResponse(total=total, items=items)


@router.post("", response_model=DeviceResponse, status_code=201)
@require_permission("asset:device:create")
async def create_device(
    req: DeviceCreate,
    current_user: dict = Depends(get_current_user),
    svc: DeviceManageService = Depends(_get_manage_svc),
):
    return await svc.create_device(req.model_dump())


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    _: dict = Depends(get_current_user),
    svc: DeviceQueryService = Depends(_get_query_svc),
):
    return await svc.get_device(device_id)


@router.post("/{device_id}/update", response_model=DeviceResponse)
@require_permission("asset:device:update")
async def update_device(
    device_id: UUID, req: DeviceUpdate,
    current_user: dict = Depends(get_current_user),
    svc: DeviceManageService = Depends(_get_manage_svc),
):
    return await svc.update_device(device_id, req.model_dump(exclude_none=True))


@router.post("/{device_id}/delete")
@require_permission("asset:device:delete")
async def delete_device(
    device_id: UUID,
    current_user: dict = Depends(get_current_user),
    svc: DeviceManageService = Depends(_get_manage_svc),
):
    await svc.delete_device(device_id)
    return {"status": "deleted", "device_id": str(device_id)}


@router.get("/{device_id}/ips")
async def get_device_ips(
    device_id: UUID,
    _: dict = Depends(get_current_user),
    svc: DeviceQueryService = Depends(_get_query_svc),
):
    device = await svc.get_device(device_id)
    return {"device_id": device_id, "ips": []}


@router.get("/{device_id}/alerts")
async def get_device_alerts(
    device_id: UUID,
    _: dict = Depends(get_current_user),
    svc: DeviceQueryService = Depends(_get_query_svc),
):
    device = await svc.get_device(device_id)
    return {"device_id": device_id, "alerts": []}


# Calibration endpoints
@cal_router.get("", response_model=CalibrationListResponse)
async def list_calibrations(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    device_id: UUID | None = None, status: str | None = None,
    _: dict = Depends(get_current_user),
    svc: CalibrationService = Depends(_get_cal_svc),
):
    total, items = await svc.list_reports(page, page_size, device_id, status)
    return CalibrationListResponse(total=total, items=items)


@cal_router.post("/run")
@require_permission("asset:calibration:execute")
async def run_calibration(
    req: CalibrationRunRequest = CalibrationRunRequest(),
    current_user: dict = Depends(get_current_user),
    svc: CalibrationService = Depends(_get_cal_svc),
):
    items = await svc.run_calibration(req.device_ids, req.source)
    return {"reports": len(items), "items": items}


@cal_router.post("/{report_id}/approve")
@require_permission("asset:calibration:approve")
async def approve_calibration(
    report_id: UUID, req: CalibrationApproveRequest,
    current_user: dict = Depends(get_current_user),
    svc: CalibrationService = Depends(_get_cal_svc),
):
    return await svc.approve_report(report_id, req.status)
