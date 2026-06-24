from fastapi import APIRouter, HTTPException

from mock_data import ALERTS

router = APIRouter(tags=["Alerts"])


@router.get("/alerts")
async def list_alerts(page: int = 1, page_size: int = 20, severity: str = "", status: str = "", device_id: str = "", source: str = ""):
    items = ALERTS
    if severity:
        items = [a for a in items if a["severity"] == severity]
    if status:
        items = [a for a in items if a["status"] == status]
    if device_id:
        items = [a for a in items if a["device_id"] == device_id]
    if source:
        items = [a for a in items if a["source"] == source]
    items = sorted(items, key=lambda a: a["time"], reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    return {"total": total, "items": items[start:start + page_size]}


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    for a in ALERTS:
        if a["id"] == alert_id:
            return a
    raise HTTPException(404, "Alert not found")


@router.get("/alerts/stats")
async def alert_stats():
    return {
        "total": len(ALERTS),
        "by_severity": {
            "critical": len([a for a in ALERTS if a["severity"] == "critical"]),
            "warning": len([a for a in ALERTS if a["severity"] == "warning"]),
            "info": len([a for a in ALERTS if a["severity"] == "info"]),
        },
        "by_status": {
            "triggered": len([a for a in ALERTS if a["status"] == "triggered"]),
            "acknowledged": len([a for a in ALERTS if a["status"] == "acknowledged"]),
            "in_progress": len([a for a in ALERTS if a["status"] == "in_progress"]),
            "resolved": len([a for a in ALERTS if a["status"] == "resolved"]),
            "closed": len([a for a in ALERTS if a["status"] == "closed"]),
            "suppressed": len([a for a in ALERTS if a["status"] == "suppressed"]),
        },
        "suppressed_count": len([a for a in ALERTS if a["status"] == "suppressed"]),
    }


@router.post("/alerts/{alert_id}/status")
async def update_alert_status(alert_id: str, body: dict):
    for a in ALERTS:
        if a["id"] == alert_id:
            a["status"] = body.get("status", a["status"])
            return a
    raise HTTPException(404, "Alert not found")
