from fastapi import APIRouter

from mock_data import ALERTS, DEVICES, SERVICES

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats")
async def dashboard_stats():
    active_alerts = [a for a in ALERTS if a["status"] in ("triggered", "acknowledged", "in_progress")]
    critical = sum(1 for a in active_alerts if a["severity"] == "critical")
    warning = sum(1 for a in active_alerts if a["severity"] == "warning")

    return {
        "total_devices": len(DEVICES),
        "online_devices": len([d for d in DEVICES if d["lifecycle_status"] == "in_use"]),
        "active_alerts": len(active_alerts),
        "critical_alerts": critical,
        "warning_alerts": warning,
        "total_services": len(SERVICES),
        "unhealthy_services": len([s for s in SERVICES if s["health"] != "healthy"]),
        "backup_success_rate": 85,
        "inspection_status": "completed",
    }


@router.get("/dashboard/alert-trend")
async def alert_trend(days: int = 7):
    return {
        "categories": ["05-22", "05-23", "05-24", "05-25", "05-26", "05-27", "05-28"],
        "series": [
            {"name": "严重", "data": [2, 1, 3, 2, 1, 2, 2], "color": "#f5222d"},
            {"name": "警告", "data": [5, 7, 8, 6, 4, 5, 6], "color": "#fa8c16"},
            {"name": "提示", "data": [10, 12, 15, 11, 8, 9, 10], "color": "#1890ff"},
            {"name": "已压制", "data": [8, 10, 12, 9, 7, 8, 15], "color": "#d9d9d9"},
        ],
    }


@router.get("/dashboard/recent-alerts")
async def recent_alerts(limit: int = 5):
    sorted_alerts = sorted(ALERTS, key=lambda a: a["time"], reverse=True)[:limit]
    return {"items": sorted_alerts}
