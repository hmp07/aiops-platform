"""EventRecordingMixin — automatic CRUD event publishing to EventWall.

Apply this mixin to any SQLAlchemy model to auto-publish
create/update/delete events without manual code in each module.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any


class EventRecordingMixin:
    """Mixin for SQLAlchemy models to auto-publish EventWall events.

    Usage:
        class Device(Base, EventRecordingMixin):
            __event_resource_type__ = "device"

    The mixin uses SQLAlchemy event listeners on `after_insert`,
    `after_update`, and `after_delete` to publish events.
    """

    __event_resource_type__: str | None = None
    __event_enabled__: bool = True

    def _build_event_payload(
        self, change_type: str, changed_fields: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return {
            "change_type": change_type,
            "changed_fields": changed_fields or {},
            "resource_id": str(getattr(self, "id", "")),
        }

    def _get_resource_name(self) -> str | None:
        for attr in ("device_name", "name", "title", "username", "display_name"):
            val = getattr(self, attr, None)
            if val:
                return str(val)
        return None

    @classmethod
    def _schedule_event_publish(
        cls,
        event_type: str,
        resource_id: str,
        resource_name: str | None,
        payload: dict[str, Any],
        severity: str = "info",
    ):
        """Fire-and-forget event publishing via the running event loop."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                cls._publish_event_async(
                    event_type, resource_id, resource_name, payload, severity
                )
            )
        except RuntimeError:
            pass  # No running loop (e.g., Celery tasks) — skip

    @classmethod
    async def _publish_event_async(
        cls,
        event_type: str,
        resource_id: str,
        resource_name: str | None,
        payload: dict[str, Any],
        severity: str,
    ):
        """Publish event to EventWall service."""
        from app.modules.module10_eventwall.service import EventService

        svc = EventService.get_instance()
        if svc:
            await svc.publish(
                event_type=event_type,
                source_module=f"module_{cls.__event_resource_type__}",
                resource_type=cls.__event_resource_type__ or "unknown",
                resource_id=resource_id,
                resource_name=resource_name,
                payload=payload,
                severity=severity,
            )


def register_event_listeners():
    """Register SQLAlchemy ORM event listeners for EventRecordingMixin.

    Called once at application startup in main.py lifespan.
    """
    from sqlalchemy import event

    from app.core.database.session import Base

    @event.listens_for(Base, "after_insert", propagate=True)
    def _on_insert(mapper, connection, target):
        if not isinstance(target, EventRecordingMixin):
            return
        if not target.__event_enabled__:
            return
        resource_type = target.__event_resource_type__
        if not resource_type:
            return
        target._schedule_event_publish(
            event_type=f"{resource_type}.created",
            resource_id=str(target.id),
            resource_name=target._get_resource_name(),
            payload=target._build_event_payload("created"),
            severity="info",
        )

    @event.listens_for(Base, "after_update", propagate=True)
    def _on_update(mapper, connection, target):
        if not isinstance(target, EventRecordingMixin):
            return
        if not target.__event_enabled__:
            return
        resource_type = target.__event_resource_type__
        if not resource_type:
            return
        # Compute changed fields from history
        changed = {}
        for attr in target.__dict__:
            if attr.startswith("_"):
                continue
            hist = getattr(target, f"_sa_{attr}_history", None)
            if hist and hist.has_changes():
                old_val = hist.deleted[0] if hist.deleted else None
                new_val = hist.added[0] if hist.added else None
                changed[attr] = {"old": str(old_val)[:200], "new": str(new_val)[:200]}
        target._schedule_event_publish(
            event_type=f"{resource_type}.updated",
            resource_id=str(target.id),
            resource_name=target._get_resource_name(),
            payload=target._build_event_payload("updated", changed),
            severity="info",
        )

    @event.listens_for(Base, "after_delete", propagate=True)
    def _on_delete(mapper, connection, target):
        if not isinstance(target, EventRecordingMixin):
            return
        if not target.__event_enabled__:
            return
        resource_type = target.__event_resource_type__
        if not resource_type:
            return
        target._schedule_event_publish(
            event_type=f"{resource_type}.deleted",
            resource_id=str(target.id),
            resource_name=target._get_resource_name(),
            payload=target._build_event_payload("deleted"),
            severity="warning",
        )
