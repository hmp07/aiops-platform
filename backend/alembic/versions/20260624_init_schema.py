"""Initial schema — all 15 tables.

Revision ID: 20260624_init
Revises:
Create Date: 2026-06-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20260624_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('email', sa.String(128), nullable=False),
        sa.Column('hashed_password', sa.String(256), nullable=False),
        sa.Column('display_name', sa.String(64), nullable=False),
        sa.Column('role', sa.String(32), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=True),
        sa.Column('username', sa.String(64), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=True),
        sa.Column('resource_id', sa.String(64), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    op.create_table('api_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('token_hash', sa.String(256), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_tokens_user_id', 'api_tokens', ['user_id'])

    op.create_table('aiops_skills',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('skill_id', sa.String(64), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(32), nullable=False, server_default='diagnosis'),
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('output_schema', postgresql.JSONB(), nullable=False),
        sa.Column('allowed_tools', postgresql.JSONB(), nullable=False),
        sa.Column('risk_level', sa.String(32), nullable=False, server_default='read_only'),
        sa.Column('module_dependencies', postgresql.JSONB(), nullable=False),
        sa.Column('is_builtin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('skill_id'),
    )

    op.create_table('agent_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('mode', sa.String(32), nullable=False, server_default='react'),
        sa.Column('skill_id', sa.String(64), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('context_page', sa.String(128), nullable=True),
        sa.Column('context_resource', postgresql.JSONB(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_sessions_user_id', 'agent_sessions', ['user_id'])

    op.create_table('agent_tool_calls',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(128), nullable=False),
        sa.Column('input_params', postgresql.JSONB(), nullable=False),
        sa.Column('output_summary', sa.String(512), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(32), nullable=False, server_default='success'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_tool_calls_session_id', 'agent_tool_calls', ['session_id'])

    op.create_table('agent_llm_calls',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(64), nullable=False),
        sa.Column('purpose', sa.String(64), nullable=False, server_default='reasoning'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_llm_calls_session_id', 'agent_llm_calls', ['session_id'])

    op.create_table('agent_preflight_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('check_type', sa.String(32), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('detail', postgresql.JSONB(), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_preflight_logs_session_id', 'agent_preflight_logs', ['session_id'])

    op.create_table('agent_pending_actions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('tool_name', sa.String(128), nullable=False),
        sa.Column('input_params', postgresql.JSONB(), nullable=False),
        sa.Column('risk_level', sa.String(32), nullable=False, server_default='write_safe'),
        sa.Column('risk_description', sa.Text(), nullable=True),
        sa.Column('rollback_plan', sa.Text(), nullable=True),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_pending_actions_session_id', 'agent_pending_actions', ['session_id'])

    op.create_table('chat_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('title', sa.String(256), nullable=False, server_default='New Chat'),
        sa.Column('agent_session_id', sa.UUID(), nullable=True),
        sa.Column('context_page', sa.String(128), nullable=True),
        sa.Column('context_resource', postgresql.JSONB(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])

    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('card_type', sa.String(32), nullable=True),
        sa.Column('card_data', postgresql.JSONB(), nullable=True),
        sa.Column('tool_calls', postgresql.JSONB(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])

    op.create_table('eventwall_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(128), nullable=False),
        sa.Column('event_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('source_module', sa.String(64), nullable=False),
        sa.Column('source_component', sa.String(128), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('producer_type', sa.String(32), nullable=False, server_default='system'),
        sa.Column('producer_user_id', sa.String(64), nullable=True),
        sa.Column('producer_agent_session_id', sa.String(64), nullable=True),
        sa.Column('correlation_id', sa.String(64), nullable=True),
        sa.Column('parent_event_id', sa.UUID(), nullable=True),
        sa.Column('root_event_id', sa.UUID(), nullable=True),
        sa.Column('fault_id', sa.String(64), nullable=True),
        sa.Column('incident_id', sa.String(64), nullable=True),
        sa.Column('resource_type', sa.String(64), nullable=True),
        sa.Column('resource_id', sa.String(128), nullable=True),
        sa.Column('resource_name', sa.String(256), nullable=True),
        sa.Column('resource_module', sa.String(64), nullable=True),
        sa.Column('severity', sa.String(16), nullable=False, server_default='info'),
        sa.Column('status', sa.String(32), nullable=False, server_default='new'),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=False),
        sa.Column('metrics', postgresql.JSONB(), nullable=False),
        sa.Column('context_ip_address', sa.String(45), nullable=True),
        sa.Column('context_user_agent', sa.String(256), nullable=True),
        sa.Column('context_request_id', sa.String(64), nullable=True),
        sa.Column('retention_ttl_days', sa.Integer(), nullable=False, server_default='90'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_eventwall_events_event_type', 'eventwall_events', ['event_type'])
    op.create_index('ix_eventwall_events_source_module', 'eventwall_events', ['source_module'])
    op.create_index('ix_eventwall_events_timestamp', 'eventwall_events', ['timestamp'])
    op.create_index('ix_eventwall_events_correlation_id', 'eventwall_events', ['correlation_id'])
    op.create_index('ix_eventwall_events_fault_id', 'eventwall_events', ['fault_id'])
    op.create_index('ix_eventwall_events_resource_type', 'eventwall_events', ['resource_type'])
    op.create_index('ix_eventwall_correlation_ts', 'eventwall_events', ['correlation_id', 'timestamp'])
    op.create_index('ix_eventwall_fault_ts', 'eventwall_events', ['fault_id', 'timestamp'])
    op.create_index('ix_eventwall_resource_ts', 'eventwall_events', ['resource_type', 'resource_id', 'timestamp'])
    op.create_index('ix_eventwall_type_module_ts', 'eventwall_events', ['event_type', 'source_module', 'timestamp'])

    op.create_table('eventwall_faults',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('fault_id', sa.String(64), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('event_ids', postgresql.JSONB(), nullable=False),
        sa.Column('event_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('top_event_type', sa.String(128), nullable=True),
        sa.Column('affected_resources', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_eventwall_faults_fault_id', 'eventwall_faults', ['fault_id'])
    op.create_index('ix_eventwall_faults_created_at', 'eventwall_faults', ['created_at'])
    op.create_index('ix_eventwall_faults_score', 'eventwall_faults', ['score', 'created_at'])

    op.create_table('eventwall_sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('source_type', sa.String(32), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auth_token_hash', sa.String(256), nullable=True),
        sa.Column('transform_config', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_eventwall_sources_source_type', 'eventwall_sources', ['source_type'])


def downgrade() -> None:
    op.drop_table('eventwall_sources')
    op.drop_table('eventwall_faults')
    op.drop_table('eventwall_events')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('agent_pending_actions')
    op.drop_table('agent_preflight_logs')
    op.drop_table('agent_llm_calls')
    op.drop_table('agent_tool_calls')
    op.drop_table('agent_sessions')
    op.drop_table('aiops_skills')
    op.drop_table('api_tokens')
    op.drop_table('audit_logs')
    op.drop_table('users')
