"""M8 AI Engine — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# Chat Session
# ============================================================

class ChatSessionCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=256)
    context_page: str | None = None
    context_resource: dict | None = None


class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: str
    title: str
    agent_session_id: UUID | None = None
    context_page: str | None = None
    message_count: int = 0
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    total: int
    items: list[ChatSessionResponse]


# ============================================================
# Chat Message
# ============================================================

class ChatMessageSend(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    skill_id: str | None = None
    analysis_only: bool = False


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    card_type: str | None = None
    card_data: dict | None = None
    tool_calls: dict | None = None
    sequence: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageListResponse(BaseModel):
    items: list[ChatMessageResponse]


# ============================================================
# Skill
# ============================================================

class SkillResponse(BaseModel):
    id: UUID
    skill_id: str
    name: str
    description: str
    category: str
    prompt_template: str
    output_schema: dict
    allowed_tools: list[str]
    risk_level: str
    module_dependencies: list[str]
    is_builtin: bool
    is_enabled: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    prompt_template: str | None = None
    output_schema: dict | None = None
    allowed_tools: list[str] | None = None
    risk_level: str | None = None
    is_enabled: bool | None = None


# ============================================================
# Agent Audit
# ============================================================

class AgentSessionResponse(BaseModel):
    id: UUID
    user_id: str
    title: str
    mode: str
    skill_id: str | None = None
    status: str
    message_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    started_at: datetime
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}


class AgentToolCallResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_number: int
    tool_name: str
    input_params: dict
    output_summary: str | None = None
    latency_ms: int = 0
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentLLMCallResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_number: int
    model_name: str
    purpose: str
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    latency_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentAuditTrailResponse(BaseModel):
    session: AgentSessionResponse
    preflight_logs: list[dict]
    tool_calls: list[AgentToolCallResponse]
    llm_calls: list[AgentLLMCallResponse]
    pending_actions: list[dict]


# ============================================================
# Pending Action
# ============================================================

class PendingActionResponse(BaseModel):
    id: UUID
    action_id: str = ""
    session_id: UUID
    tool_name: str
    risk_level: str
    risk_description: str | None = None
    rollback_plan: str | None = None
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ActionConfirmRequest(BaseModel):
    reason: str | None = None


class ActionRejectRequest(BaseModel):
    reason: str = ""


# ============================================================
# Suggestions
# ============================================================

class SuggestionsResponse(BaseModel):
    suggestions: list[str]
    page: str


# ============================================================
# SSE Event (for typing)
# ============================================================

class SSEEvent(BaseModel):
    event: str
    data: dict
