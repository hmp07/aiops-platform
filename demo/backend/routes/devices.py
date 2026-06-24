from fastapi import APIRouter, HTTPException

from mock_data import DEVICES

router = APIRouter(tags=["Devices"])


@router.get("/devices")
async def list_devices(page: int = 1, page_size: int = 20, device_type: str = "", vendor: str = "", lifecycle_status: str = "", keyword: str = ""):
    items = DEVICES
    if device_type:
        items = [d for d in items if d["device_type"] == device_type]
    if vendor:
        items = [d for d in items if d["vendor"] == vendor]
    if lifecycle_status:
        items = [d for d in items if d["lifecycle_status"] == lifecycle_status]
    if keyword:
        kw = keyword.lower()
        items = [d for d in items if kw in d["device_name"].lower() or kw in d["management_ip"] or kw in d["model"].lower()]
    total = len(items)
    start = (page - 1) * page_size
    return {"total": total, "items": items[start:start + page_size]}


@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    for d in DEVICES:
        if d["id"] == device_id:
            return d
    raise HTTPException(404, "Device not found")


@router.get("/devices/{device_id}/ips")
async def get_device_ips(device_id: str):
    from mock_data import IP_ALLOCATIONS
    return {"items": [ip for ip in IP_ALLOCATIONS if ip.get("device_id") == device_id]}


@router.get("/devices/{device_id}/alerts")
async def get_device_alerts(device_id: str):
    from mock_data import ALERTS
    return {"items": [a for a in ALERTS if a["device_id"] == device_id]}
