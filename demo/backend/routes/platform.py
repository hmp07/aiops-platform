from fastapi import APIRouter

from mock_data import AUDIT_LOGS, USERS

router = APIRouter(tags=["Platform"])


@router.get("/users")
async def list_users(page: int = 1, page_size: int = 20, role: str = ""):
    items = USERS
    if role:
        items = [u for u in items if u["role"] == role]
    return {"total": len(items), "items": items}


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    for u in USERS:
        if u["id"] == user_id:
            return {k: v for k, v in u.items() if k != "password"}
    return None


@router.get("/audit")
async def query_audit(page: int = 1, page_size: int = 50, user_id: str = "", action: str = "", resource_type: str = ""):
    items = AUDIT_LOGS
    if user_id:
        items = [e for e in items if e["user_id"] == user_id]
    if action:
        items = [e for e in items if e["action"] == action]
    if resource_type:
        items = [e for e in items if e["resource_type"] == resource_type]
    items = sorted(items, key=lambda e: e["created_at"], reverse=True)
    return {"total": len(items), "items": items}


@router.get("/tokens")
async def list_tokens():
    return {"items": []}
