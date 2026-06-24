"""M4 Log — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class LogSourceCreate(BaseModel):
    name: str; source_type: str = "syslog"; host: str | None = None; config: dict = {}

class LogSourceResponse(BaseModel):
    id: UUID; name: str; source_type: str; host: str | None = None
    config: dict; is_enabled: bool; created_at: datetime
    model_config = {"from_attributes": True}

class LogEntryResponse(BaseModel):
    id: UUID; time: datetime; device_id: UUID | None = None
    source: str; facility: str | None = None; severity: str
    hostname: str | None = None; message: str; parsed_fields: dict
    model_config = {"from_attributes": True}

class LogListResponse(BaseModel): total: int; items: list[LogEntryResponse]

class LogIngestRequest(BaseModel):
    messages: list[dict]; source: str = "api"
