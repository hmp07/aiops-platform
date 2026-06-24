from fastapi import APIRouter, HTTPException

from mock_data import USERS

router = APIRouter(tags=["Auth"])


@router.post("/auth/login")
async def login(body: dict):
    username = body.get("username", "")
    password = body.get("password", "")
    for u in USERS:
        if u["username"] == username and u["password"] == password:
            if not u["is_active"]:
                raise HTTPException(401, "Account disabled")
            return {
                "access_token": f"demo-token-{u['id']}-{u['role']}",
                "token_type": "bearer",
                "expires_in": 28800,
                "user": {
                    "id": u["id"], "username": u["username"], "email": u["email"],
                    "display_name": u["display_name"], "role": u["role"],
                    "is_active": u["is_active"], "last_login_at": u["last_login_at"],
                    "created_at": u["created_at"],
                },
            }
    raise HTTPException(401, "Invalid username or password")


@router.get("/auth/me")
async def get_me():
    u = USERS[0]
    return {
        "id": u["id"], "username": u["username"], "email": u["email"],
        "display_name": u["display_name"], "role": u["role"],
        "is_active": u["is_active"], "last_login_at": u["last_login_at"],
        "created_at": u["created_at"],
    }
