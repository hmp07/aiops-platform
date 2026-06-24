"""M5 Config — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BackupTriggerRequest(BaseModel):
    device_ids: list[UUID] | None = None


class BackupResponse(BaseModel):
    id: UUID
    device_id: UUID
    backup_type: str
    status: str
    file_size: int
    file_path: str | None = None
    config_hash: str | None = None
    backup_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class BackupListResponse(BaseModel):
    total: int
    items: list[BackupResponse]


class DiffResponse(BaseModel):
    id: UUID
    device_id: UUID
    old_backup_id: UUID
    new_backup_id: UUID
    diff_content: str | None = None
    risk_level: str
    created_at: datetime
    model_config = {"from_attributes": True}


class DiffListResponse(BaseModel):
    total: int
    items: list[DiffResponse]


class RollbackRequest(BaseModel):
    pass


class BatchOperationResponse(BaseModel):
    id: UUID
    operation_type: str
    device_ids: list[UUID]
    status: str
    result_summary: dict
    created_at: datetime
    model_config = {"from_attributes": True}
