"""Built-in tool: query_alert — real DB query."""
from app.modules.module8_ai.tools.base import BaseTool, ToolSpec


class QueryAlertTool(BaseTool):
    spec = ToolSpec(
        tool_id="query_alert",
        name="Query Alert",
        description="Query alert records by severity, status, device, or source. "
                    "Returns alert details including title, severity, status, and time.",
        parameters={
            "type": "object",
            "properties": {
                "severity": {"type": "string", "description": "Alert severity: critical, warning, info"},
                "status": {"type": "string", "description": "Alert status: triggered, acknowledged, resolved, closed"},
                "device_id": {"type": "string", "description": "Device ID to filter alerts for a specific device"},
                "source": {"type": "string", "description": "Alert source: zabbix, itop, signoz, custom"},
            },
        },
        required_permissions=["monitoring:alert:list"],
        risk_level="read_only",
        timeout_seconds=10,
        module="module3_monitoring",
    )

    async def execute(self, **kwargs) -> dict:
        from app.core.database.session import async_session_factory
        from app.modules.module3_monitoring.repository import AlertRepository
        from uuid import UUID

        severity = kwargs.get("severity")
        status = kwargs.get("status")
        device_id = kwargs.get("device_id")
        source = kwargs.get("source")

        async with async_session_factory() as db:
            repo = AlertRepository(db)
            total, items = await repo.list_all(
                1, 20, severity, status,
                UUID(device_id) if device_id else None,
                source,
            )
            return {
                "found": total,
                "alerts": [
                    {"id": str(a.id), "title": a.title, "severity": a.severity,
                     "status": a.status, "source": a.source or "unknown",
                     "time": a.time.isoformat() if a.time else None}
                    for a in items[:10]
                ],
            }
