"""M3 Monitoring — Alert state machine, rules engine, suppression, evidence."""
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.module3_monitoring.repository import (
    AlertRepository, AlertRuleRepository, ChannelRepository,
    EvidenceRepository, MetricRepository, PolicyRepository,
)

VALID_TRANSITIONS = {
    "triggered": ["acknowledged", "suppressed"],
    "acknowledged": ["in_progress", "resolved"],
    "in_progress": ["resolved"],
    "resolved": ["closed"],
    "closed": [],
    "suppressed": [],
}


class AlertService:
    def __init__(self, repo: AlertRepository, evidence_repo: EvidenceRepository):
        self._repo = repo; self._evidence = evidence_repo

    async def list_alerts(self, page=1, page_size=20, severity=None, status=None,
                          device_id=None, source=None) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(page, page_size, severity, status, device_id, source)
        return total, [self._to_dict(r) for r in rows]

    async def get_alert(self, alert_id: UUID) -> dict | None:
        obj = await self._repo.get_by_id(alert_id)
        if not obj: return None
        result = self._to_dict(obj)
        evidence = await self._evidence.get_by_alert(alert_id)
        if evidence:
            result["evidence"] = {
                "config_snapshot": evidence.config_snapshot,
                "log_fragment": evidence.log_fragment,
                "interface_status": evidence.interface_status,
            }
        return result

    async def create_alert(self, data: dict) -> dict:
        data["id"] = data.get("id", uuid.uuid4())
        data["time"] = data.get("time", datetime.now(timezone.utc))
        obj = await self._repo.create(data)
        return self._to_dict(obj)

    async def create_from_webhook(self, data: dict) -> dict:
        """Create alert from external webhook. Applies suppression check."""
        device_id_str = data.get("device_id")
        title = data.get("title", "")
        metric_name = data.get("metric_name", "")

        # Suppression check: same device + similar title in last 5 min
        if device_id_str:
            try:
                did = UUID(device_id_str)
                recent = await self._repo.find_recent(did, title[:30], minutes=5)
                if recent:
                    return self._to_dict(recent)  # Duplicate suppressed
            except ValueError:
                pass

        obj = await self._repo.create({
            "id": uuid.uuid4(),
            "time": datetime.now(timezone.utc),
            "device_id": device_id_str,
            "severity": data.get("severity", "warning"),
            "status": "triggered",
            "title": title,
            "description": data.get("description", ""),
            "source": data.get("source", "webhook"),
        })
        return self._to_dict(obj)

    async def acknowledge(self, alert_id: UUID, user_id: str) -> dict:
        return await self._transition(alert_id, "acknowledged", {"acknowledged_by": user_id})

    async def resolve(self, alert_id: UUID, user_id: str) -> dict:
        return await self._transition(alert_id, "resolved", {"resolved_by": user_id})

    async def close(self, alert_id: UUID, user_id: str = "") -> dict:
        return await self._transition(alert_id, "closed", {"resolved_by": user_id})

    async def get_stats(self) -> dict:
        _, rows = await self._repo.list_all(1, 1000, None, None, None, None)
        by_sev = {"critical": 0, "warning": 0, "info": 0}
        by_st = {"triggered": 0, "acknowledged": 0, "in_progress": 0, "resolved": 0, "closed": 0, "suppressed": 0}
        for r in rows:
            s = r.severity; by_sev[s] = by_sev.get(s, 0) + 1 if s in by_sev else None
            st = r.status; by_st[st] = by_st.get(st, 0) + 1 if st in by_st else None
        return {"total": len(rows), "by_severity": by_sev, "by_status": by_st,
                "suppressed_count": by_st.get("suppressed", 0)}

    async def _transition(self, alert_id: UUID, new_status: str, extra: dict) -> dict:
        obj = await self._repo.get_by_id(alert_id)
        if not obj:
            raise NotFoundError("Alert not found")
        current = obj.status
        if new_status not in VALID_TRANSITIONS.get(current, []):
            from app.core.exceptions import ValidationError
            raise ValidationError(f"Cannot transition from '{current}' to '{new_status}'")
        data = {"status": new_status, **extra}
        obj = await self._repo.update(obj, data)
        return self._to_dict(obj)

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "time": obj.time, "device_id": obj.device_id,
            "rule_id": obj.rule_id, "severity": obj.severity, "status": obj.status,
            "title": obj.title, "description": obj.description, "source": obj.source,
            "root_cause": obj.root_cause, "suppressed_by": obj.suppressed_by,
            "acknowledged_by": obj.acknowledged_by, "resolved_by": obj.resolved_by,
            "created_at": obj.created_at, "updated_at": obj.updated_at,
        }


class AlertRuleService:
    def __init__(self, repo: AlertRuleRepository):
        self._repo = repo

    async def list_rules(self, page=1, page_size=20) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(page, page_size)
        return total, [self._to_dict(r) for r in rows]

    async def create_rule(self, data: dict) -> dict:
        obj = await self._repo.create(data)
        return self._to_dict(obj)

    async def update_rule(self, rule_id: UUID, data: dict) -> dict:
        obj = await self._repo.get_by_id(rule_id)
        if not obj: raise NotFoundError("Rule not found")
        obj = await self._repo.update(obj, data)
        return self._to_dict(obj)

    async def delete_rule(self, rule_id: UUID):
        obj = await self._repo.get_by_id(rule_id)
        if not obj: raise NotFoundError("Rule not found")
        await self._repo.delete(obj)

    def _to_dict(self, obj) -> dict:
        return {"id": obj.id, "name": obj.name, "rule_type": obj.rule_type,
                "metric_name": obj.metric_name, "condition": obj.condition,
                "threshold": obj.threshold, "duration_seconds": obj.duration_seconds,
                "severity": obj.severity, "is_enabled": obj.is_enabled,
                "created_at": obj.created_at, "updated_at": obj.updated_at}


class NotificationService:
    def __init__(self, ch_repo: ChannelRepository, pol_repo: PolicyRepository):
        self._ch = ch_repo; self._pol = pol_repo

    async def list_channels(self) -> list[dict]: return [self._ch_to_dict(r) for r in await self._ch.list_all()]
    async def create_channel(self, data: dict) -> dict: return self._ch_to_dict(await self._ch.create(data))
    async def list_policies(self) -> list[dict]: return [self._pol_to_dict(r) for r in await self._pol.list_all()]
    async def create_policy(self, data: dict) -> dict: return self._pol_to_dict(await self._pol.create(data))

    def _ch_to_dict(self, obj) -> dict:
        return {"id": obj.id, "channel_type": obj.channel_type, "name": obj.name,
                "config": obj.config, "is_enabled": obj.is_enabled, "created_at": obj.created_at}
    def _pol_to_dict(self, obj) -> dict:
        return {"id": obj.id, "name": obj.name, "channel_id": obj.channel_id,
                "severity_filter": obj.severity_filter, "device_filter": obj.device_filter,
                "is_enabled": obj.is_enabled, "created_at": obj.created_at}
