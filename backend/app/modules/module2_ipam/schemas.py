"""M2 IPAM — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SubnetCreate(BaseModel):
    cidr: str = Field(min_length=1, max_length=64)
    vlan_id: int | None = None
    gateway: str | None = None
    description: str | None = None


class SubnetUpdate(BaseModel):
    cidr: str | None = None
    vlan_id: int | None = None
    gateway: str | None = None
    description: str | None = None


class SubnetResponse(BaseModel):
    id: UUID
    cidr: str
    vlan_id: int | None = None
    gateway: str | None = None
    description: str | None = None
    total_ips: int
    used_ips: int
    created_at: datetime
    model_config = {"from_attributes": True}


class SubnetListResponse(BaseModel):
    total: int
    items: list[SubnetResponse]


class IPAllocationCreate(BaseModel):
    subnet_id: UUID
    ip_address: str = Field(min_length=1)
    device_id: UUID | None = None
    interface_name: str | None = None


class IPAllocationRelease(BaseModel):
    pass


class IPAllocationResponse(BaseModel):
    id: UUID
    subnet_id: UUID
    ip_address: str
    status: str
    device_id: UUID | None = None
    interface_name: str | None = None
    source: str
    allocated_at: datetime | None = None
    released_at: datetime | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class IPAllocationListResponse(BaseModel):
    total: int
    items: list[IPAllocationResponse]
