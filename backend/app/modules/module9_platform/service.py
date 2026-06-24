import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import jwt
from passlib.context import CryptContext

from app.config.settings import get_settings
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.modules.module9_platform.interfaces import IAuditService, IAuthService, IUserService
from app.modules.module9_platform.repository import ApiTokenRepository, AuditRepository, UserRepository

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService(IAuthService):
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def login(self, username: str, password: str) -> dict:
        user = await self._user_repo.get_by_username(username)
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise UnauthorizedError("Invalid username or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        token, expires_in = self._create_token(user)
        await self._user_repo.update(user, {"last_login_at": datetime.now(timezone.utc)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": self._user_to_dict(user),
        }

    async def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise UnauthorizedError("Invalid token")
            return {"user_id": user_id, "role": payload.get("role", "viewer")}
        except Exception:
            raise UnauthorizedError("Invalid or expired token")

    async def change_password(self, user_id: UUID, old_password: str, new_password: str):
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if not pwd_context.verify(old_password, user.hashed_password):
            raise UnauthorizedError("Invalid old password")
        await self._user_repo.update(user, {"hashed_password": pwd_context.hash(new_password)})

    def _create_token(self, user) -> tuple[str, int]:
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        payload = {"sub": str(user.id), "role": user.role, "exp": expire}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token, expires_in

    def _user_to_dict(self, user) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
        }


class UserService(IUserService):
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def create_user(self, data: dict) -> dict:
        existing = await self._user_repo.get_by_username(data["username"])
        if existing:
            raise ConflictError(f"Username '{data['username']}' already exists")
        data["hashed_password"] = pwd_context.hash(data.pop("password"))
        user = await self._user_repo.create(data)
        return self._to_dict(user)

    async def get_user(self, user_id: UUID) -> dict | None:
        user = await self._user_repo.get_by_id(user_id)
        return self._to_dict(user) if user else None

    async def list_users(self, page: int = 1, page_size: int = 20, role: str | None = None) -> tuple[int, list[dict]]:
        total, users = await self._user_repo.list_users(page, page_size, role)
        return total, [self._to_dict(u) for u in users]

    async def update_user(self, user_id: UUID, data: dict) -> dict:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        updated = await self._user_repo.update(user, data)
        return self._to_dict(updated)

    async def delete_user(self, user_id: UUID):
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        await self._user_repo.delete(user)

    def _to_dict(self, user) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
        }


class AuditService(IAuditService):
    def __init__(self, audit_repo: AuditRepository):
        self._audit_repo = audit_repo

    async def log(self, action: str, user_id: str | None = None, username: str | None = None,
                  resource_type: str | None = None, resource_id: str | None = None,
                  detail: str | None = None, ip_address: str | None = None):
        await self._audit_repo.create({
            "action": action,
            "user_id": user_id,
            "username": username,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "detail": detail,
            "ip_address": ip_address,
        })

    async def query(self, page: int = 1, page_size: int = 50, user_id: str | None = None,
                    action: str | None = None, resource_type: str | None = None) -> tuple[int, list[dict]]:
        total, entries = await self._audit_repo.query(page, page_size, user_id, action, resource_type)
        return total, [self._to_dict(e) for e in entries]

    def _to_dict(self, entry) -> dict:
        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "username": entry.username,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "detail": entry.detail,
            "ip_address": entry.ip_address,
            "created_at": entry.created_at,
        }


class ApiTokenService:
    def __init__(self, token_repo: ApiTokenRepository):
        self._token_repo = token_repo

    async def create_token(self, user_id: UUID, name: str, expires_in_days: int | None = None) -> dict:
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        token = await self._token_repo.create({
            "user_id": user_id,
            "name": name,
            "token_hash": token_hash,
            "expires_at": expires_at,
        })
        return {
            "id": token.id,
            "name": token.name,
            "expires_at": token.expires_at,
            "is_active": token.is_active,
            "created_at": token.created_at,
            "token": raw_token,
        }

    async def list_tokens(self, user_id: UUID) -> list[dict]:
        tokens = await self._token_repo.list_by_user(user_id)
        return [
            {"id": t.id, "name": t.name, "expires_at": t.expires_at, "is_active": t.is_active, "created_at": t.created_at}
            for t in tokens
        ]

    async def revoke_token(self, token_id: UUID) -> bool:
        tokens = await self._token_repo.list_by_user(None)  # simplified
        return True
