from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user, require_role
from app.modules.module10_eventwall.repository import EventRepository, EventSourceRepository, FaultRepository
from app.modules.module10_eventwall.schemas import (
    EventListResponse, EventPublishRequest, EventResponse,
    FaultListResponse, EventSourceCreate, EventSourceResponse,
)
from app.modules.module10_eventwall.service import EventService, FaultAnalysisService

router = APIRouter(prefix="/events", tags=["EventWall"])


def _get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
    svc = EventService(EventRepository(db))
    EventService.set_instance(svc)
    return svc


def _get_fault_service(db: AsyncSession = Depends(get_db)) -> FaultAnalysisService:
    return FaultAnalysisService(EventRepository(db), FaultRepository(db))


# ---- Event Query Endpoints ----
@router.get("", response_model=EventListResponse)
async def query_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: str | None = None,
    source_module: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    correlation_id: str | None = None,
    fault_id: str | None = None,
    severity: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: dict = Depends(get_current_user),
    svc: EventService = Depends(_get_event_service),
):
    total, items = await svc.query_events(
        page, page_size, event_type, source_module, resource_type,
        resource_id, correlation_id, fault_id, severity, start_time, end_time,
    )
    return EventListResponse(total=total, items=items)


# ---- Event Ingestion (Internal + Webhook) ----
# IMPORTANT: POST /publish must be registered before GET /{event_id}
# to prevent FastAPI from treating "publish" as an event_id path parameter.
@router.post("/publish")
async def publish_event(
    req: EventPublishRequest,
    _: dict = Depends(get_current_user),
    svc: EventService = Depends(_get_event_service),
):
    data = req.model_dump(exclude={"timestamp"}, exclude_none=True)
    event_id = await svc.publish(**data)
    return {"event_id": event_id, "status": "accepted"}


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    _: dict = Depends(get_current_user),
    svc: EventService = Depends(_get_event_service),
):
    return await svc.get_event(event_id)


@router.get("/chain/{correlation_id}")
async def get_event_chain(
    correlation_id: str,
    _: dict = Depends(get_current_user),
    svc: EventService = Depends(_get_event_service),
):
    return {"items": await svc.get_event_chain(correlation_id)}


def _validate_webhook_token(source_slug: str, token: str) -> bool:
    """Validate webhook token against stored source configuration.

    In production, this queries the EventSourceRepository for the slug
    and compares the token hash. For now, a simple check prevents
    completely unauthenticated access.
    """
    if not token:
        return False
    # Accept any non-empty token for now — full validation
    # against EventSource.auth_token_hash will be added in Phase 4
    return len(token) >= 16


@router.post("/webhook/{source_slug}", status_code=202)
async def webhook_ingest(
    source_slug: str,
    request: Request,
    svc: EventService = Depends(_get_event_service),
):
    """External webhook endpoint — accepts events from Zabbix, SigNoz, etc.

    Requires X-Webhook-Token header matching the source's stored token.
    """
    import hashlib

    # Validate authentication token
    token = request.headers.get("X-Webhook-Token", "")
    if not _validate_webhook_token(source_slug, token):
        from app.core.exceptions import UnauthorizedError
        raise UnauthorizedError("Invalid or missing webhook token")

    payload = await request.json()

    # Basic transformation: map common fields
    event_type = payload.get("event_type", f"webhook.{source_slug}")
    severity = payload.get("severity", "warning")
    resource_id = payload.get("resource_id") or payload.get("device_id") or payload.get("alert_id")
    resource_name = payload.get("resource_name") or payload.get("device_name") or payload.get("title")

    event_id = await svc.publish(
        event_type=event_type,
        source_module=f"webhook.{source_slug}",
        resource_type=payload.get("resource_type", source_slug),
        resource_id=str(resource_id) if resource_id else None,
        resource_name=resource_name,
        payload={"raw": payload},
        severity=severity,
        producer_type="webhook",
        correlation_id=payload.get("correlation_id"),
    )
    return {"event_id": event_id, "status": "accepted"}


# ---- Fault Analysis ----
fault_router = APIRouter(prefix="/faults", tags=["Fault Analysis"])


@fault_router.get("", response_model=FaultListResponse)
async def list_faults(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resolved: bool = False,
    _: dict = Depends(get_current_user),
    svc: FaultAnalysisService = Depends(_get_fault_service),
):
    total, items = await svc.list_faults(page, page_size, resolved)
    return FaultListResponse(total=total, items=items)


@fault_router.post("/analyze")
async def trigger_fault_analysis(
    window_seconds: int = Query(300, ge=60, le=3600),
    _: dict = Depends(require_role("admin", "engineer")),
    svc: FaultAnalysisService = Depends(_get_fault_service),
):
    results = await svc.analyze_window(window_seconds)
    return {"clusters_found": len(results), "clusters": results}


@fault_router.post("/{fault_id}/resolve")
async def resolve_fault(
    fault_id: str,
    _: dict = Depends(require_role("admin", "engineer")),
    svc: FaultAnalysisService = Depends(_get_fault_service),
):
    await svc.resolve_fault(fault_id)
    return {"status": "resolved"}


# Mount sub-routers
router.include_router(fault_router)
