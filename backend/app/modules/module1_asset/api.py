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

    # Find the Zabbix datasource so we get the right URL + auth
    from app.core.database.session import async_session_factory
    from app.modules.module11_scheduler.repository import DataSourceRepository
    from app.modules.module11_scheduler.service import DataSourceService

    zabbix = None
    async with async_session_factory() as sdb:
        ds_repo = DataSourceRepository(sdb)
        ds_svc = DataSourceService(ds_repo)
        # Pick the first enabled zabbix datasource
        all_ds = await ds_svc.list_all()
        for ds_obj in all_ds:
            if ds_obj.get("source_type") == "zabbix" and ds_obj.get("is_enabled"):
                zabbix = ds_svc._get_adapter(
                    await ds_repo.get_by_id(ds_obj["id"])
                )
                break

    if not zabbix:
        from app.integrations.zabbix.client import ZabbixAdapter
        zabbix = ZabbixAdapter()

    now_ts = int(datetime.now(timezone.utc).timestamp())
    hour_ago_ts = now_ts - 3600

    # ---- KPI snapshot via item.get ----
    items = await zabbix.get_items(hostid, [
        "system.cpu.util",
        "vm.memory.utilization",
        "vfs.fs",               # matches vfs.fs.size + vfs.fs.dependent.size
        "net.if.in",
        "net.if.out",
    ])
    kpi = _extract_kpis(items)

    # ---- History for trend chart (CPU / memory / disk) ----
    cpu_hist = await zabbix.get_history(hostid, "system.cpu.util[,idle]", hour_ago_ts, now_ts)
    mem_hist = await zabbix.get_history(hostid, "vm.memory.utilization", hour_ago_ts, now_ts)
    disk_hist = await zabbix.get_history(hostid, "vfs.fs.size", hour_ago_ts, now_ts)  # matches dependent + non-dependent

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
        elif "vfs.fs" in key and "pused" in key:
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


# ── Asset Matching ────────────────────────────────────────────


@router.post("/matches/run")
@require_permission("asset:device:update")
async def run_asset_matching(
    current_user: dict = Depends(get_current_user),
):
    """Run cross-source asset matching (Zabbix ↔ iTop).

    Returns candidates for manual review and auto-merged count.
    """
    from app.core.database.session import async_session_factory
    from app.modules.module1_asset.match_service import AssetMatchService

    async with async_session_factory() as db:
        svc = AssetMatchService(db)
        result = await svc.find_candidates()
        return {
            "merged": result.merged,
            "skipped": result.skipped,
            "candidates": [
                {
                    "device_a": {"id": c.device_a["id"], "name": c.device_a["device_name"],
                                 "source": (c.device_a.get("extra_attrs") or {}).get("source"),
                                 "ip": c.device_a.get("management_ip")},
                    "device_b": {"id": c.device_b["id"], "name": c.device_b["device_name"],
                                 "source": (c.device_b.get("extra_attrs") or {}).get("source"),
                                 "ip": c.device_b.get("management_ip")},
                    "score": c.score,
                    "rule": c.rule,
                    "reason": c.reason,
                }
                for c in result.candidates
            ],
        }


@router.post("/matches/confirm")
@require_permission("asset:device:update")
async def confirm_match(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Manually confirm a candidate match between two devices."""
    from uuid import UUID as _UUID
    from app.core.database.session import async_session_factory
    from app.modules.module1_asset.match_service import AssetMatchService

    async with async_session_factory() as db:
        svc = AssetMatchService(db)
        return await svc.confirm_merge(
            _UUID(body["device_a_id"]),
            _UUID(body["device_b_id"]),
        )


# ── Zabbix → iTop Enrichment ─────────────────────────────────


@router.post("/matches/enrich")
@require_permission("asset:device:update")
async def enrich_device(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Push Zabbix-collected data (serial, OS, model) to iTop CI.

    Expects: {device_id: UUID} for a merged device that has both
    Zabbix hostid and iTop ci_id in extra_attrs.
    """
    from uuid import UUID as _UUID
    from app.core.database.session import async_session_factory
    from app.integrations.zabbix.client import ZabbixAdapter
    from app.integrations.itop.client import ItopAdapter
    from app.modules.module1_asset.enrichment import EnrichmentService
    from app.modules.module11_scheduler.repository import DataSourceRepository
    from app.modules.module11_scheduler.service import DataSourceService

    device_id = _UUID(body["device_id"])

    async with async_session_factory() as db:
        # Load device
        from app.modules.module1_asset.models import Device
        from sqlalchemy import select

        dev = (await db.execute(
            select(Device).where(Device.id == device_id, Device.deleted_at.is_(None))
        )).scalar_one_or_none()

        if not dev:
            return {"status": "error", "message": "Device not found"}

        extra = dev.extra_attrs or {}
        zabbix_hostid = extra.get("hostid")
        itop_class = extra.get("ci_class")
        itop_id = extra.get("ci_id")

        if not zabbix_hostid or not itop_id:
            return {"status": "error",
                    "message": "Device must have both Zabbix hostid and iTop ci_id"}

        # Get adapter instances from datasources
        ds_repo = DataSourceRepository(db)
        ds_svc = DataSourceService(ds_repo)

        zabbix_adapter = None
        itop_adapter = None
        for ds_obj in await ds_svc.list_all():
            if not ds_obj.get("is_enabled"):
                continue
            ds_entity = await ds_repo.get_by_id(ds_obj["id"])
            if ds_obj["source_type"] == "zabbix" and not zabbix_adapter:
                zabbix_adapter = ds_svc._get_adapter(ds_entity)
            elif ds_obj["source_type"] == "itop" and not itop_adapter:
                itop_adapter = ds_svc._get_adapter(ds_entity)

        if not zabbix_adapter or not itop_adapter:
            return {"status": "error", "message": "Both Zabbix and iTop datasources must be configured"}

        enrichment = EnrichmentService(zabbix_adapter, itop_adapter)
        result = await enrichment.enrich(zabbix_hostid, itop_class, itop_id)
        return result


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
