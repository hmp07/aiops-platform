import logging
from collections.abc import Awaitable, Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config.settings import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if credentials is None:
        raise UnauthorizedError("Missing authentication token")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Invalid token payload")
        return {"user_id": user_id, "role": payload.get("role", "viewer")}
    except JWTError as e:
        raise UnauthorizedError(f"Invalid token: {str(e)}")


def require_role(*roles: str) -> Callable[[dict], Awaitable[dict]]:
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise ForbiddenError(f"Requires one of roles: {roles}")
        return user

    return role_checker
