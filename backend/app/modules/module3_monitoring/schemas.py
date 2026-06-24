"""M3 Monitoring — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AlertRuleCreate(BaseModel):
    name: str; rule_type: str = "threshold"; metric_name: str
    condition: str = "gt"; threshold: float = 0.0
    duration_seconds: int = 60; severity: str = "warning"; is_enabled: bool = True

class AlertRuleUpdate(BaseModel):
    name: str | None = None; threshold: float | None = None
    severity: str | None = None; is_enabled: bool | None = None

class AlertRuleResponse(BaseModel):
    id: UUID; name: str; rule_type: str; metric_name: str
    condition: str; threshold: float; severity: str; is_enabled: bool
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}

class AlertRuleListResponse(BaseModel):
    total: int; items: list[AlertRuleResponse]


class AlertResponse(BaseModel):
    id: UUID; time: datetime; device_id: UUID | None = None
    rule_id: UUID | None = None; severity: str; status: str
    title: str; description: str | None = None; source: str
    root_cause: dict | None = None; suppressed_by: UUID | None = None
    acknowledged_by: str | None = None; resolved_by: str | None = None
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}

class AlertDetailResponse(AlertResponse):
    evidence: dict | None = None

class AlertListResponse(BaseModel):
    total: int; items: list[AlertResponse]

class AlertStatsResponse(BaseModel):
    total: int; by_severity: dict; by_status: dict; suppressed_count: int

class AlertWebhookRequest(BaseModel):
    device_id: str | None = None; title: str; description: str | None = None
    severity: str = "warning"; source: str = "webhook"
    rule_name: str | None = None; metric_name: str | None = None


class ChannelCreate(BaseModel):
    channel_type: str = Field(pattern="^(wecom|email|sms)$")
    name: str; config: dict = Field(default_factory=dict)

class ChannelResponse(BaseModel):
    id: UUID; channel_type: str; name: str; config: dict; is_enabled: bool; created_at: datetime
    model_config = {"from_attributes": True}


class PolicyCreate(BaseModel):
    name: str; channel_id: UUID; severity_filter: list = Field(default_factory=list)
    device_filter: dict = Field(default_factory=dict)

class PolicyResponse(BaseModel):
    id: UUID; name: str; channel_id: UUID; severity_filter: list
    device_filter: dict; is_enabled: bool; created_at: datetime
    model_config = {"from_attributes": True}


class MetricQuery(BaseModel):
    device_id: UUID; metric_name: str = "cpu_usage"
    start_time: str | None = None; end_time: str | None = None
