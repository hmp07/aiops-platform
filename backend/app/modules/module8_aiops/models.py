"""M8 AIOps — Data Models (sxdevops architecture, 12 tables)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base


# ── Model Provider (imported from module8_ai to avoid duplicate table) ──
# AIOpsModelProvider table already defined in module8_ai.models, reuse it.
from app.modules.module8_ai.models import ModelProvider as AIOpsModelProvider


# ── Agent Config ───────────────────────────────────────────

class AIOpsAgentConfig(Base):
    __tablename__ = "aiops_agent_configs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    default_provider_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("aiops_model_providers.id"), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    welcome_message: Mapped[str] = mapped_column(Text, default="")
    suggested_questions: Mapped[list] = mapped_column(JSONB, default=list)
    enabled_skill_ids: Mapped[list] = mapped_column(JSONB, default=list)
    enabled_mcp_server_ids: Mapped[list] = mapped_column(JSONB, default=list)
    allow_action_execution: Mapped[bool] = mapped_column(Boolean, default=False)
    require_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    show_evidence: Mapped[bool] = mapped_column(Boolean, default=True)
    max_history_messages: Mapped[int] = mapped_column(Integer, default=20)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── MCP Server ─────────────────────────────────────────────

class AIOpsMCPServer(Base):
    __tablename__ = "aiops_mcp_servers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    server_type: Mapped[str] = mapped_column(String(32), default="http")  # http / stdio / builtin
    endpoint_or_command: Mapped[str] = mapped_column(String(512), nullable=False)
    auth_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    tool_whitelist: Mapped[list] = mapped_column(JSONB, default=list)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── Skill ──────────────────────────────────────────────────

class AIOpsSkill(Base):
    __tablename__ = "aiops_skills_new"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(32), default="diagnosis")
    content: Mapped[str] = mapped_column(Text, nullable=False)  # SOP 文本
    output_contract: Mapped[dict] = mapped_column(JSONB, default=dict)
    builtin_tools: Mapped[list] = mapped_column(JSONB, default=list)
    recommended_tools: Mapped[list] = mapped_column(JSONB, default=list)
    applicable_actions: Mapped[list] = mapped_column(JSONB, default=list)
    risk_level: Mapped[str] = mapped_column(String(32), default="read_only")
    source_type: Mapped[str] = mapped_column(String(32), default="inline")  # inline / local
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── Chat Session ───────────────────────────────────────────

class AIOpsChatSession(Base):
    __tablename__ = "aiops_chat_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), default="New Chat")
    context: Mapped[dict] = mapped_column(JSONB, default=dict)  # page_context, environment
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── Chat Message ───────────────────────────────────────────

class AIOpsChatMessage(Base):
    __tablename__ = "aiops_chat_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("aiops_chat_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user / assistant
    content: Mapped[str] = mapped_column(Text, default="")
    message_type: Mapped[str] = mapped_column(String(32), default="")  # "" / "error"
    processing_status: Mapped[str | None] = mapped_column(String(16), nullable=True)  # pending / running / completed / failed
    blocks: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # structured response blocks
    citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pending_action_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    extra_meta: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)  # processing_steps, tool_events, error_code
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Pending Action ─────────────────────────────────────────

class AIOpsPendingAction(Base):
    __tablename__ = "aiops_pending_actions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("aiops_chat_sessions.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), default="")
    risk_level: Mapped[str] = mapped_column(String(16), default="medium")
    action_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    result_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending / confirmed / executed / canceled
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Tool Invocation Audit ──────────────────────────────────

class AIOpsToolInvocation(Base):
    __tablename__ = "aiops_tool_invocations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_summary: Mapped[str] = mapped_column(Text, default="")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Model Invocation Audit ─────────────────────────────────

class AIOpsModelInvocation(Base):
    __tablename__ = "aiops_model_invocations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), default="reasoning")
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Knowledge Environment ──────────────────────────────────

class AIOpsKnowledgeEnvironment(Base):
    __tablename__ = "aiops_knowledge_environments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    aliases: Mapped[list] = mapped_column(JSONB, default=list)
    env_type: Mapped[str] = mapped_column(String(32), default="production")
    metric_datasource_ids: Mapped[list] = mapped_column(JSONB, default=list)
    log_datasource_ids: Mapped[list] = mapped_column(JSONB, default=list)
    trace_datasource_ids: Mapped[list] = mapped_column(JSONB, default=list)
    k8s_cluster_ids: Mapped[list] = mapped_column(JSONB, default=list)
    association_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── External Task (A2A) ────────────────────────────────────

class AIOpsExternalTask(Base):
    __tablename__ = "aiops_external_tasks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    source_agent: Mapped[str] = mapped_column(String(64), default="")
    action_code: Mapped[str] = mapped_column(String(64), default="")
    agent_mode: Mapped[str] = mapped_column(String(16), default="react")
    plan_steps: Mapped[list] = mapped_column(JSONB, default=list)
    orchestration_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    agent_results: Mapped[dict] = mapped_column(JSONB, default=dict)
    react_trace: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── Runbook ────────────────────────────────────────────────

class AIOpsRunbook(Base):
    __tablename__ = "aiops_runbooks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(32), default="incident")
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft / published / archived
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
