"""M3 Monitoring — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module3_monitoring.repository import (
    AlertRepository, AlertRuleRepository, ChannelRepository,
    EvidenceRepository, MetricRepository, PolicyRepository,
)
from app.modules.module3_monitoring.schemas import (
    AlertDetailResponse, AlertListResponse, AlertRuleCreate, AlertRuleListResponse,
    AlertRuleResponse, AlertRuleUpdate, AlertStatsResponse, AlertWebhookRequest,
    ChannelCreate, ChannelResponse, MetricQuery, PolicyCreate, PolicyResponse,
)
from app.modules.module3_monitoring.service import AlertRuleService, AlertService, NotificationService

router = APIRouter(prefix="/alerts", tags=["Monitoring"])
rule_router = APIRouter(prefix="/rules", tags=["Alert Rules"])
notif_router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _get_alert_svc(db: AsyncSession = Depends(get_db)) -> AlertService:
    return AlertService(AlertRepository(db), EvidenceRepository(db))

def _get_rule_svc(db: AsyncSession = Depends(get_db)) -> AlertRuleService:
    return AlertRuleService(AlertRuleRepository(db))

def _get_notif_svc(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(ChannelRepository(db), PolicyRepository(db))


# ---- Alerts ----
@router.get("", response_model=AlertListResponse)
async def list_alerts(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    severity: str | None = None, status: str | None = None,
    device_id: UUID | None = None, source: str | None = None,
    _: dict = Depends(get_current_user), svc: AlertService = Depends(_get_alert_svc)):
    total, items = await svc.list_alerts(page, page_size, severity, status, device_id, source)
    return AlertListResponse(total=total, items=items)

@router.post("/webhook", status_code=201)
async def webhook_trigger(req: AlertWebhookRequest, svc: AlertService = Depends(_get_alert_svc)):
    result = await svc.create_from_webhook(req.model_dump())
    return result

@router.get("/stats", response_model=AlertStatsResponse)
async def alert_stats(_: dict = Depends(get_current_user), svc: AlertService = Depends(_get_alert_svc)):
    return await svc.get_stats()

@router.get("/{alert_id}", response_model=AlertDetailResponse)
async def get_alert(alert_id: UUID, _: dict = Depends(get_current_user),
                    svc: AlertService = Depends(_get_alert_svc)):
    return await svc.get_alert(alert_id)

@router.post("/{alert_id}/acknowledge")
@require_permission("monitoring:alert:acknowledge")
async def acknowledge(alert_id: UUID, current_user: dict = Depends(get_current_user),
                      svc: AlertService = Depends(_get_alert_svc)):
    return await svc.acknowledge(alert_id, current_user["user_id"])

@router.post("/{alert_id}/resolve")
@require_permission("monitoring:alert:resolve")
async def resolve(alert_id: UUID, current_user: dict = Depends(get_current_user),
                  svc: AlertService = Depends(_get_alert_svc)):
    return await svc.resolve(alert_id, current_user["user_id"])

@router.post("/{alert_id}/close")
@require_permission("monitoring:alert:close")
async def close(alert_id: UUID, current_user: dict = Depends(get_current_user),
                svc: AlertService = Depends(_get_alert_svc)):
    return await svc.close(alert_id)


# ---- Rules ----
@rule_router.get("", response_model=AlertRuleListResponse)
async def list_rules(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user), svc: AlertRuleService = Depends(_get_rule_svc)):
    total, items = await svc.list_rules(page, page_size)
    return AlertRuleListResponse(total=total, items=items)

@rule_router.post("", response_model=AlertRuleResponse, status_code=201)
@require_permission("monitoring:rule:create")
async def create_rule(req: AlertRuleCreate, current_user: dict = Depends(get_current_user),
                      svc: AlertRuleService = Depends(_get_rule_svc)):
    return await svc.create_rule(req.model_dump())

@rule_router.post("/{rule_id}/update", response_model=AlertRuleResponse)
@require_permission("monitoring:rule:update")
async def update_rule(rule_id: UUID, req: AlertRuleUpdate,
    current_user: dict = Depends(get_current_user), svc: AlertRuleService = Depends(_get_rule_svc)):
    return await svc.update_rule(rule_id, req.model_dump(exclude_none=True))

@rule_router.post("/{rule_id}/delete")
@require_permission("monitoring:rule:delete")
async def delete_rule(rule_id: UUID, current_user: dict = Depends(get_current_user),
                      svc: AlertRuleService = Depends(_get_rule_svc)):
    await svc.delete_rule(rule_id)
    return {"status": "deleted", "rule_id": str(rule_id)}


# ---- Notifications ----
@notif_router.get("/channels", response_model=list[ChannelResponse])
async def list_channels(_: dict = Depends(get_current_user), svc: NotificationService = Depends(_get_notif_svc)):
    return await svc.list_channels()

@notif_router.post("/channels", response_model=ChannelResponse, status_code=201)
@require_permission("monitoring:notification:manage")
async def create_channel(req: ChannelCreate, current_user: dict = Depends(get_current_user),
                         svc: NotificationService = Depends(_get_notif_svc)):
    return await svc.create_channel(req.model_dump())

@notif_router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(_: dict = Depends(get_current_user), svc: NotificationService = Depends(_get_notif_svc)):
    return await svc.list_policies()

@notif_router.post("/policies", response_model=PolicyResponse, status_code=201)
@require_permission("monitoring:notification:manage")
async def create_policy(req: PolicyCreate, current_user: dict = Depends(get_current_user),
                        svc: NotificationService = Depends(_get_notif_svc)):
    return await svc.create_policy(req.model_dump())


# ---- Metrics ----
@router.get("/metrics/{device_id}")
async def get_metrics(device_id: UUID, metric_name: str = Query("cpu_usage"),
    _: dict = Depends(get_current_user)):
    from app.modules.module3_monitoring.repository import MetricRepository
    from app.core.database.session import async_session_factory
    async with async_session_factory() as db:
        repo = MetricRepository(db)
        rows = await repo.query(device_id, metric_name, limit=50)
        return {"device_id": str(device_id), "metric": metric_name, "points": [
            {"time": r.time.isoformat(), "value": r.metric_value} for r in rows
        ]}
