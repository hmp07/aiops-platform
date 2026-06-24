from fastapi import APIRouter

from mock_data import CONFIG_BACKUPS, CONFIG_DIFF

router = APIRouter(tags=["Configs"])


@router.get("/configs/backups")
async def list_backups(device_id: str = "", status: str = "", page: int = 1, page_size: int = 20):
    items = CONFIG_BACKUPS
    if device_id:
        items = [b for b in items if b["device_id"] == device_id]
    if status:
        items = [b for b in items if b["status"] == status]
    items = sorted(items, key=lambda b: b["backup_at"], reverse=True)
    return {"total": len(items), "items": items}


@router.get("/configs/backups/{backup_id}")
async def get_backup(backup_id: str):
    for b in CONFIG_BACKUPS:
        if b["id"] == backup_id:
            return b
    return None


@router.get("/configs/diff/{device_id}")
async def get_config_diff(device_id: str):
    if device_id == CONFIG_DIFF["device_id"]:
        return CONFIG_DIFF
    return {"message": "No diff available for this device"}


@router.get("/configs/stats")
async def config_stats():
    return {
        "total_backups": len(CONFIG_BACKUPS),
        "success_count": len([b for b in CONFIG_BACKUPS if b["status"] == "success"]),
        "failed_count": len([b for b in CONFIG_BACKUPS if b["status"] == "failed"]),
        "success_rate": 80,
    }
