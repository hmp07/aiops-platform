"""EventWall service — publish, query, fault analysis."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.settings import get_settings
from app.modules.module10_eventwall.interfaces import IEventService, IFaultAnalysisService
from app.modules.module10_eventwall.repository import EventRepository, FaultRepository

settings = get_settings()


class EventService(IEventService):
    _instance: "EventService | None" = None

    def __init__(self, event_repo: EventRepository):
        self._repo = event_repo

    @classmethod
    def get_instance(cls) -> "EventService | None":
        return cls._instance

    @classmethod
    def set_instance(cls, instance: "EventService"):
        cls._instance = instance

    async def publish(
        self,
        event_type: str,
        source_module: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        resource_name: str | None = None,
        payload: dict[str, Any] | None = None,
        severity: str = "info",
        correlation_id: str | None = None,
        parent_event_id: str | None = None,
        fault_id: str | None = None,
        producer_type: str = "system",
        producer_user_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> str:
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        data = {
            "id": event_id,
            "event_type": event_type,
            "source_module": source_module,
            "timestamp": now,
            "received_at": now,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_name": resource_name,
            "severity": severity,
            "status": "new",
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "parent_event_id": parent_event_id,
            "fault_id": fault_id,
            "payload": payload or {},
            "tags": tags or {},
            "metrics": {},
            "producer_type": producer_type,
            "producer_user_id": producer_user_id,
        }
        await self._repo.create(data)
        return event_id

    async def query_events(
        self,
        page: int = 1,
        page_size: int = 50,
        event_type: str | None = None,
        source_module: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        fault_id: str | None = None,
        severity: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        return await self._repo.query(
            page, page_size, event_type, source_module, resource_type,
            resource_id, correlation_id, fault_id, severity, start_time, end_time,
        )

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        row = await self._repo.get_by_id(event_id)
        return self._to_dict(row) if row else None

    async def get_event_chain(self, correlation_id: str) -> list[dict[str, Any]]:
        rows = await self._repo.get_by_correlation(correlation_id)
        return [self._to_dict(r) for r in rows]

    def _to_dict(self, row) -> dict[str, Any]:
        return {
            "id": row.id, "event_type": row.event_type,
            "source_module": row.source_module, "timestamp": row.timestamp,
            "received_at": row.received_at, "resource_type": row.resource_type,
            "resource_id": row.resource_id, "resource_name": row.resource_name,
            "severity": row.severity, "status": row.status,
            "correlation_id": row.correlation_id, "fault_id": row.fault_id,
            "payload": row.payload, "tags": row.tags, "metrics": row.metrics,
            "producer_type": row.producer_type, "producer_user_id": row.producer_user_id,
        }


class FaultAnalysisService(IFaultAnalysisService):
    SEVERITY_WEIGHTS = {"emergency": 10, "critical": 5, "warning": 2, "info": 1, "debug": 0.5}

    def __init__(self, event_repo: EventRepository, fault_repo: FaultRepository):
        self._event_repo = event_repo
        self._fault_repo = fault_repo

    async def analyze_window(self, window_seconds: int = 300) -> list[dict[str, Any]]:
        """Correlate events in the recent window into fault clusters."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(seconds=window_seconds)
        events = await self._event_repo.query_time_window(start, now)

        # Group by correlation_id, then by resource proximity
        clusters: dict[str, dict[str, Any]] = {}
        for e in events:
            key = e.correlation_id or str(e.id)
            if key not in clusters:
                clusters[key] = {
                    "event_ids": [], "events": [],
                    "max_severity": "info", "total_weight": 0.0,
                    "resource_types": set(), "top_event_type": None,
                }
            c = clusters[key]
            c["event_ids"].append(str(e.id))
            c["events"].append(e)
            c["total_weight"] += self.SEVERITY_WEIGHTS.get(e.severity, 0)
            if self.SEVERITY_WEIGHTS.get(e.severity, 0) > self.SEVERITY_WEIGHTS.get(c["max_severity"], 0):
                c["max_severity"] = e.severity
            if e.resource_type:
                c["resource_types"].add(e.resource_type)
            c["top_event_type"] = e.event_type

        # Convert to fault clusters
        results = []
        for key, c in clusters.items():
            if c["total_weight"] < 3:  # skip low-signal clusters
                continue
            fault_id = str(uuid.uuid4())
            summary = self._generate_summary(c)
            results.append({
                "fault_id": fault_id,
                "score": c["total_weight"],
                "event_ids": c["event_ids"],
                "event_count": len(c["event_ids"]),
                "summary": summary,
                "top_event_type": c["top_event_type"],
                "affected_resources": list(c["resource_types"]),
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        # Persist top clusters
        for r in results[:10]:
            await self._fault_repo.create(r)

        return results

    async def get_fault(self, fault_id: str) -> dict[str, Any] | None:
        row = await self._fault_repo.get_by_fault_id(fault_id)
        return self._fault_to_dict(row) if row else None

    async def list_faults(
        self, page: int = 1, page_size: int = 20, resolved: bool = False
    ) -> tuple[int, list[dict[str, Any]]]:
        total, rows = await self._fault_repo.list_faults(page, page_size, resolved)
        return total, [self._fault_to_dict(r) for r in rows]

    async def resolve_fault(self, fault_id: str):
        await self._fault_repo.resolve(fault_id)

    def _generate_summary(self, cluster: dict) -> str:
        events = cluster["events"]
        if not events:
            return "No events"
        event_types = set(e.event_type for e in events)
        resources = set(e.resource_name for e in events if e.resource_name)
        parts = [
            f"Fault cluster: {len(events)} events",
            f"Types: {', '.join(list(event_types)[:3])}",
        ]
        if resources:
            parts.append(f"Resources: {', '.join(list(resources)[:3])}")
        return " | ".join(parts)

    def _fault_to_dict(self, row) -> dict[str, Any]:
        return {
            "id": row.id, "fault_id": row.fault_id, "score": row.score,
            "event_ids": row.event_ids, "event_count": row.event_count,
            "summary": row.summary, "top_event_type": row.top_event_type,
            "affected_resources": row.affected_resources,
            "created_at": row.created_at, "resolved_at": row.resolved_at,
        }
