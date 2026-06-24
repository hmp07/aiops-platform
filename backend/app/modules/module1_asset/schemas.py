"""M1 Asset — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    device_name: str = Field(min_length=1, max_length=128)
    device_type: str = Field(min_length=1, max_length=64)
    vendor: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=128)
    serial_number: str | None = None
    software_version: str | None = None
    management_ip: str | None = None
    location: str | None = None
    cabinet: str | None = None
    lifecycle_status: str = "in_use"
    business_system: str | None = None
    user_department: str | None = None
    up_link_device_id: UUID | None = None
    up_link_port: str | None = None
    extra_attrs: dict = Field(default_factory=dict, serialization_alias="metadata")


class DeviceUpdate(BaseModel):
    device_name: str | None = None
    device_type: str | None = None
    vendor: str | None = None
    model: str | None = None
    serial_number: str | None = None
    software_version: str | None = None
    management_ip: str | None = None
    location: str | None = None
    cabinet: str | None = None
    lifecycle_status: str | None = None
    business_system: str | None = None
    user_department: str | None = None
    up_link_device_id: UUID | None = None
    up_link_port: str | None = None
    extra_attrs: dict | None = Field(default=None, serialization_alias="metadata")


class DeviceResponse(BaseModel):
    id: UUID
    device_name: str
    device_type: str
    vendor: str
    model: str
    serial_number: str | None = None
    software_version: str | None = None
    management_ip: str | None = None
    location: str | None = None
    cabinet: str | None = None
    lifecycle_status: str
    business_system: str | None = None
    user_department: str | None = None
    up_link_device_id: UUID | None = None
    up_link_port: str | None = None
    last_backup_status: str | None = None
    last_backup_at: datetime | None = None
    last_inspection_status: str | None = None
    last_inspection_at: datetime | None = None
    extra_attrs: dict = Field(serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    total: int
    items: list[DeviceResponse]


class CalibrationResponse(BaseModel):
    id: UUID
    device_id: UUID
    source: str
    field_name: str
    current_value: str | None = None
    discovered_value: str | None = None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class CalibrationListResponse(BaseModel):
    total: int
    items: list[CalibrationResponse]


class CalibrationRunRequest(BaseModel):
    device_ids: list[UUID] | None = None
    source: str = "snmp"


class CalibrationApproveRequest(BaseModel):
    status: str = Field(pattern="^(confirmed|rejected)$")
