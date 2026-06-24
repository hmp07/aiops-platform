"""Built-in tool: query_alert — mock implementation."""
from app.modules.module8_ai.tools.base import BaseTool, ToolSpec

MOCK_ALERTS = [
    {"id": "a1", "title": "CORE-SW-01 CPU 飙升至 95%", "severity": "critical",
     "device_id": "d1", "status": "acknowledged", "source": "zabbix",
     "time": "2026-05-29T08:00:00Z", "description": "核心交换机 CPU 异常"},
    {"id": "a2", "title": "支付服务 P99 延迟突增至 3500ms", "severity": "critical",
     "device_id": "d11", "status": "in_progress", "source": "signoz",
     "time": "2026-05-29T09:00:00Z", "description": "支付服务响应延迟"},
    {"id": "a3", "title": "AGG-SW-01 Gi1/0/24 CRC 错误率异常", "severity": "warning",
     "device_id": "d3", "status": "triggered", "source": "zabbix",
     "time": "2026-05-29T07:00:00Z", "description": "接口错误包增长"},
    {"id": "a5", "title": "SRV-DB-01 磁盘使用率达到 85%", "severity": "warning",
     "device_id": "d13", "status": "resolved", "source": "zabbix",
     "time": "2026-05-29T02:00:00Z", "description": "磁盘空间不足"},
    {"id": "a9", "title": "ROUTER-01 BGP 邻居状态 Down", "severity": "critical",
     "device_id": "d9", "status": "resolved", "source": "zabbix",
     "time": "2026-05-28T22:00:00Z", "description": "出口路由器 BGP 中断"},
]


class QueryAlertTool(BaseTool):
    spec = ToolSpec(
        tool_id="query_alert",
        name="Query Alert",
        description="Query active and historical alerts by device ID, severity, "
                    "status, or time range. Returns alert details.",
        parameters={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Filter by device ID"},
                "severity": {"type": "string", "description": "critical, warning, info"},
                "status": {"type": "string", "description": "triggered, acknowledged, in_progress, resolved, closed"},
                "limit": {"type": "integer", "description": "Max results (default 10)"},
            },
        },
        required_permissions=["monitoring:alert:list"],
        risk_level="read_only",
        timeout_seconds=10,
        module="module3_monitoring",
    )

    async def execute(self, **kwargs) -> dict:
        device_id = kwargs.get("device_id", "")
        severity = kwargs.get("severity", "")
        status = kwargs.get("status", "")
        limit = kwargs.get("limit", 10)

        results = MOCK_ALERTS
        if device_id:
            results = [a for a in results if a["device_id"] == device_id]
        if severity:
            results = [a for a in results if a["severity"] == severity]
        if status:
            results = [a for a in results if a["status"] == status]

        return {
            "found": len(results),
            "alerts": results[:limit],
        }
