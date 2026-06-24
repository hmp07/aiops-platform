"""Domain Event Bus using Redis Streams for lightweight pub/sub.

Event schema:
{
    "event_id": "<uuid>",
    "event_type": "alert.triggered",
    "source_module": "module3_monitoring",
    "timestamp": "2026-05-28T10:30:00Z",
    "payload": { ... },
    "correlation_id": null,
    "tenant_id": null
}
"""

import json
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from app.core.cache.redis import get_redis

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]

_subscribers: dict[str, list[EventHandler]] = {}


def subscribe(event_type: str, handler: EventHandler):
    """Register an async handler for a given event type."""
    _subscribers.setdefault(event_type, []).append(handler)


async def publish(
    event_type: str,
    payload: dict[str, Any],
    *,
    source_module: str = "system",
    correlation_id: str | None = None,
    tenant_id: str | None = None,
    severity: str = "info",
):
    """Publish a domain event to Redis Stream and persist to EventWall.

    Events go to two destinations:
      1. Redis Streams — for in-process subscribers (fast dispatch)
      2. EventWall database — for persistent audit trail (via fire-and-forget)
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "source_module": source_module,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "correlation_id": correlation_id,
        "tenant_id": tenant_id,
        "severity": severity,
    }

    # Publish to Redis Stream for external consumers
    redis = await get_redis()
    await redis.xadd(f"events:{event_type}", {"data": json.dumps(event)}, maxlen=10000)

    # Notify in-process subscribers
    for handler in _subscribers.get(event_type, []):
        await handler(event)

    # Persist to EventWall (fire-and-forget, non-blocking)
    try:
        from app.modules.module10_eventwall.service import EventService
        evt_svc = EventService.get_instance()
        if evt_svc:
            await evt_svc.publish(
                event_type=event_type,
                source_module=source_module,
                payload=payload,
                severity=severity,
                correlation_id=correlation_id,
            )
    except Exception:
        pass  # EventWall persistence failure must not block event bus
