from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EventPublishRequest(BaseModel):
    event_type: str = Field(max_length=128)
    source_module: str = Field(default="external", max_length=64)
    resource_type: str | None = Field(default=None, max_length=64)
    resource_id: str | None = Field(default=None, max_length=128)
    resource_name: str | None = None
    payload: dict = Field(default_factory=dict)
    severity: str = Field(default="info", pattern="^(info|debug|warning|critical|emergency)$")
    correlation_id: str | None = None
    parent_event_id: str | None = None
    fault_id: str | None = None
    producer_type: str = Field(default="webhook", pattern="^(system|webhook|user|agent)$")
    producer_user_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    timestamp: str | None = None  # ISO8601, defaults to now


class EventResponse(BaseModel):
    id: UUID
    event_type: str
    source_module: str
    timestamp: datetime
    received_at: datetime
    resource_type: str | None
    resource_id: str | None
    resource_name: str | None
    severity: str
    status: str
    correlation_id: str | None
    fault_id: str | None
    payload: dict
    tags: dict
    metrics: dict
    producer_type: str
    producer_user_id: str | None

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    total: int
    items: list[EventResponse]


class FaultClusterResponse(BaseModel):
    id: UUID
    fault_id: str
    score: float
    event_ids: list[str]
    event_count: int
    summary: str | None
    top_event_type: str | None
    affected_resources: list[dict]
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class FaultListResponse(BaseModel):
    total: int
    items: list[FaultClusterResponse]


class EventSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    source_type: str = Field(pattern="^(zabbix|signoz|grafana|jenkins|gitlab|custom)$")
    slug: str = Field(min_length=1, max_length=64)
    description: str | None = None
    is_enabled: bool = True
    auth_token: str | None = None
    transform_config: dict = Field(default_factory=dict)


class EventSourceResponse(BaseModel):
    id: UUID
    name: str
    source_type: str
    slug: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
