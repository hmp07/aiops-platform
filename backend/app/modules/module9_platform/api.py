from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user, require_role
from app.modules.module9_platform.repository import ApiTokenRepository, AuditRepository, UserRepository
from app.modules.module9_platform.schemas import (
    ApiTokenCreate,
    ApiTokenCreateResponse,
    ApiTokenResponse,
    AuditLogListResponse,
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.modules.module9_platform.service import ApiTokenService, AuditService, AuthService, UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/users", tags=["Users"])
audit_router = APIRouter(prefix="/audit", tags=["Audit Log"])


def _get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def _get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


def _get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(AuditRepository(db))


def _get_token_service(db: AsyncSession = Depends(get_db)) -> ApiTokenService:
    return ApiTokenService(ApiTokenRepository(db))


# ---- Auth endpoints ----
@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, auth: AuthService = Depends(_get_auth_service)):
    return await auth.login(req.username, req.password)


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    auth: AuthService = Depends(_get_auth_service),
):
    from uuid import UUID
    await auth.change_password(UUID(current_user["user_id"]), req.old_password, req.new_password)
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    user_svc: UserService = Depends(_get_user_service),
):
    from uuid import UUID
    user = await user_svc.get_user(UUID(current_user["user_id"]))
    return user


# ---- User management endpoints ----
@user_router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    _: dict = Depends(require_role("admin")),
    user_svc: UserService = Depends(_get_user_service),
):
    total, items = await user_svc.list_users(page, page_size, role)
    return UserListResponse(total=total, items=items)


@user_router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    req: UserCreate,
    _: dict = Depends(require_role("admin")),
    user_svc: UserService = Depends(_get_user_service),
    audit: AuditService = Depends(_get_audit_service),
    request: Request = None,
):
    user = await user_svc.create_user(req.model_dump())
    return user


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _: dict = Depends(require_role("admin")),
    user_svc: UserService = Depends(_get_user_service),
):
    from uuid import UUID
    user = await user_svc.get_user(UUID(user_id))
    return user


@user_router.post("/{user_id}/update", response_model=UserResponse)
async def update_user(
    user_id: str,
    req: UserUpdate,
    _: dict = Depends(require_role("admin")),
    user_svc: UserService = Depends(_get_user_service),
):
    from uuid import UUID
    return await user_svc.update_user(UUID(user_id), req.model_dump(exclude_none=True))


@user_router.post("/{user_id}/delete")
async def delete_user(
    user_id: str,
    _: dict = Depends(require_role("admin")),
    user_svc: UserService = Depends(_get_user_service),
):
    from uuid import UUID
    await user_svc.delete_user(UUID(user_id))
    return {"status": "deleted", "user_id": user_id}


# ---- Audit endpoints ----
@audit_router.get("", response_model=AuditLogListResponse)
async def query_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    _: dict = Depends(require_role("admin")),
    audit: AuditService = Depends(_get_audit_service),
):
    total, items = await audit.query(page, page_size, user_id, action, resource_type)
    return AuditLogListResponse(total=total, items=items)


# ---- API Token endpoints ----
token_router = APIRouter(prefix="/tokens", tags=["API Tokens"])


@token_router.post("", response_model=ApiTokenCreateResponse, status_code=201)
async def create_token(
    req: ApiTokenCreate,
    current_user: dict = Depends(get_current_user),
    token_svc: ApiTokenService = Depends(_get_token_service),
):
    from uuid import UUID
    return await token_svc.create_token(UUID(current_user["user_id"]), req.name, req.expires_in_days)


@token_router.get("", response_model=list[ApiTokenResponse])
async def list_tokens(
    current_user: dict = Depends(get_current_user),
    token_svc: ApiTokenService = Depends(_get_token_service),
):
    from uuid import UUID
    return await token_svc.list_tokens(UUID(current_user["user_id"]))


# Attach sub-routers
router.include_router(user_router)
router.include_router(audit_router)
router.include_router(token_router)
