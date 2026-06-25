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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
):
    """Fetch alerts for a specific device."""
    from app.core.database.session import async_session_factory
    from app.modules.module3_monitoring.repository import AlertRepository

    async with async_session_factory() as db:
        repo = AlertRepository(db)
        total, items = await repo.list_all(page, page_size, None, None, device_id, None)
        return {
            "device_id": str(device_id),
            "total": total,
            "alerts": [
                {
                    "id": str(a.id), "time": a.time.isoformat(), "severity": a.severity,
                    "status": a.status, "title": a.title, "source": a.source,
                }
                for a in items
            ],
        }


@router.post("/{device_id}/metrics")
async def get_device_metrics(
    device_id: UUID,
    _: dict = Depends(get_current_user),
    svc: DeviceQueryService = Depends(_get_query_svc),
):
    """Fetch real-time Zabbix metrics for a device.

    Looks up the Zabbix hostid from the device's extra_attrs,
    then queries Zabbix for CPU / memory / disk / network KPIs
    and 1-hour history for the trend chart.
    """
    from datetime import datetime, timezone

    device = await svc.get_device(device_id)
    if not device:
        return {"device_id": str(device_id), "monitored": False}

    extra = (device.get("extra_attrs") or {}) if isinstance(device, dict) else getattr(device, "extra_attrs", None) or {}
    hostid = extra.get("hostid") or extra.get("host", {}).get("hostid")
    if not hostid:
        return {"device_id": str(device_id), "monitored": False}

    from app.integrations.zabbix.client import ZabbixAdapter

    zabbix = ZabbixAdapter()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    hour_ago_ts = now_ts - 3600

    # ---- KPI snapshot via item.get ----
    items = await zabbix.get_items(hostid, [
        "system.cpu.util[,idle]",
        "vm.memory.utilization",
        "vfs.fs.size[/,pused]",
        "net.if.in[",
        "net.if.out[",
    ])
    kpi = _extract_kpis(items)

    # ---- History for trend chart (CPU / memory / disk) ----
    cpu_hist = await zabbix.get_history(hostid, "system.cpu.util[,idle]", hour_ago_ts, now_ts)
    mem_hist = await zabbix.get_history(hostid, "vm.memory.utilization", hour_ago_ts, now_ts)
    disk_hist = await zabbix.get_history(hostid, "vfs.fs.size[/,pused]", hour_ago_ts, now_ts)

    return {
        "device_id": str(device_id),
        "monitored": True,
        "kpi": kpi,
        "trends": {
            "cpu": [_cpu_usage_point(p) for p in cpu_hist],
            "memory": [_float_point(p) for p in mem_hist],
            "disk": [_float_point(p) for p in disk_hist],
        },
    }


# ── helpers for get_device_metrics ────────────────────────────

def _extract_kpis(items: list[dict]) -> dict:
    """Extract KPI snapshot values from Zabbix item.get response."""
    kpi: dict[str, float | None] = {
        "cpu": None, "memory": None, "disk": None,
        "network_in": None, "network_out": None,
    }
    for item in items:
        key = item.get("key_", "")
        raw = item.get("lastvalue")
        if raw is None:
            continue
        try:
            val = float(raw)
        except (ValueError, TypeError):
            continue
        if "system.cpu.util[,idle]" in key:
            kpi["cpu"] = round(100.0 - val, 1)
        elif "vm.memory.utilization" in key:
            kpi["memory"] = round(val, 1)
        elif "vfs.fs.size[/,pused]" in key:
            kpi["disk"] = round(val, 1)
        elif "net.if.in" in key and kpi["network_in"] is None:
            kpi["network_in"] = round(val / 1_000_000, 2)
        elif "net.if.out" in key and kpi["network_out"] is None:
            kpi["network_out"] = round(val / 1_000_000, 2)
    return kpi


def _float_point(point: dict) -> dict:
    return {"clock": point["clock"], "value": float(point.get("value", 0))}


def _cpu_usage_point(point: dict) -> dict:
    """Convert CPU idle → usage %."""
    try:
        usage = round(100.0 - float(point.get("value", 0)), 1)
    except (ValueError, TypeError):
        usage = 0.0
    return {"clock": point["clock"], "value": usage}


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
