from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---- User ----
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=64)
    role: str = Field(default="viewer", pattern="^(admin|engineer|viewer)$")


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = None
    role: str | None = Field(default=None, pattern="^(admin|engineer|viewer)$")
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]


# ---- Auth ----
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ---- Audit ----
class AuditLogResponse(BaseModel):
    id: UUID
    user_id: str | None
    username: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    detail: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogResponse]


# ---- API Token ----
class ApiTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


class ApiTokenResponse(BaseModel):
    id: UUID
    name: str
    expires_at: datetime | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiTokenCreateResponse(ApiTokenResponse):
    token: str  # only returned once at creation
