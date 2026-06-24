"""M6 APM — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    name: str; display_name: str; language: str = "unknown"
    host_ids: list[UUID] = []; health: str = "healthy"

class ServiceUpdate(BaseModel):
    display_name: str | None = None; p99_latency_ms: float | None = None
    error_rate_pct: float | None = None; throughput_rps: float | None = None
    health: str | None = None; host_ids: list[UUID] | None = None

class ServiceResponse(BaseModel):
    id: UUID; name: str; display_name: str; language: str
    instances: int; host_ids: list; p99_latency_ms: float
    error_rate_pct: float; throughput_rps: float; health: str
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}

class ServiceListResponse(BaseModel): total: int; items: list[ServiceResponse]

class EdgeCreate(BaseModel):
    source_service_id: UUID; target_service_id: UUID
    latency_ms: float = 0; rps: float = 0; status: str = "healthy"

class EdgeResponse(BaseModel):
    id: UUID; source_service_id: UUID; target_service_id: UUID
    latency_ms: float; rps: float; status: str; created_at: datetime
    model_config = {"from_attributes": True}

class TopologyResponse(BaseModel):
    nodes: list[dict]; edges: list[dict]

class CrossLayerResponse(BaseModel):
    service_id: UUID; host_ids: list; switch_ids: list
    context: dict; updated_at: datetime
    model_config = {"from_attributes": True}
