"""M8 AI Engine — Agent dispatch and session management."""
import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from app.modules.module8_ai.agent.executor import AgentExecutor
from app.modules.module8_ai.agent.pending_action import PendingActionManager
from app.modules.module8_ai.interfaces import IAgentService, ISkillService
from app.modules.module8_ai.llm.client import LLMClient
from app.modules.module8_ai.repository import (
    AgentSessionRepository, ChatMessageRepository, ChatSessionRepository,
    LLMCallRepository, PendingActionRepository, PreflightLogRepository,
    SkillRepository, ToolCallRepository,
)
from app.modules.module8_ai.tools.registry import ToolRegistry

SUGGESTIONS_MAP = {
    "/dashboard": ["当前系统整体健康状态如何？", "最近有哪些需要关注的告警？", "本周巡检有哪些重点？"],
    "/asset": ["哪些设备配置备份失败了？", "最近有设备状态变更吗？", "CORE-SW-01 的运行状态如何？"],
    "/monitoring/alerts": ["这个告警可能影响哪些业务？", "最近1小时该设备有异常吗？", "类似告警的历史处理方案是什么？"],
    "/apm/services": ["支付服务最近1小时有异常吗？", "数据库慢查询影响了哪些业务？", "服务拓扑中有哪些异常依赖？"],
    "/apm/topology": ["当前网络拓扑健康状态怎么样？", "交换机 ACC-SW-01 上联了哪些服务？"],
    "/config/backups": ["最近有哪些配置变更？是否异常？", "哪些设备的配置备份失败了？"],
    "default": ["支付服务最近1小时有异常吗？", "CORE-SW-01的CPU为什么这么高？", "最近有哪些配置变更？"],
}


class AgentService(IAgentService):
    def __init__(
        self,
        chat_repo: ChatSessionRepository,
        chat_msg_repo: ChatMessageRepository,
        agent_repo: AgentSessionRepository,
        tool_repo: ToolCallRepository,
        llm_repo: LLMCallRepository,
        preflight_repo: PreflightLogRepository,
        pending_repo: PendingActionRepository,
        skill_repo: SkillRepository,
    ):
        self._chat = chat_repo
        self._msgs = chat_msg_repo
        self._agent = agent_repo
        self._tools = tool_repo
        self._llm = llm_repo
        self._preflight = preflight_repo
        self._pending = pending_repo
        self._skill = skill_repo
        self._executor = AgentExecutor()

    async def create_session(
        self, user: dict, title: str = "New Chat",
        context_page: str | None = None, context_resource: dict | None = None,
    ) -> dict:
        data = {
            "user_id": user.get("user_id", ""),
            "title": title,
            "context_page": context_page,
            "context_resource": context_resource or {},
        }
        obj = await self._chat.create(data)
        return self._chat_to_dict(obj)

    async def send_message(
        self, session_id: uuid.UUID, content: str, user: dict,
        skill_id: str | None = None, analysis_only: bool = False,
    ) -> AsyncIterator[str]:
        # Load session
        chat = await self._chat.get(session_id)
        if not chat:
            yield self._sse_error("Session not found")
            return

        # Save user message
        seq = await self._msgs.get_max_sequence(session_id) + 1
        await self._msgs.create({
            "session_id": session_id, "role": "user",
            "content": content, "sequence": seq,
        })

        # Load skill if specified
        skill = None
        if skill_id:
            skill = await self._skill.get_by_skill_id(skill_id)

        # Update session
        await self._chat.update(chat, {
            "message_count": chat.message_count + 1,
            "last_message_at": datetime.now(timezone.utc),
        })

        # Create agent session for audit
        agent_session = await self._agent.create({
            "user_id": user.get("user_id", ""),
            "title": content[:100],
            "mode": "react",
            "skill_id": skill_id,
            "status": "active",
            "context_page": chat.context_page,
            "started_at": datetime.now(timezone.utc),
        })

        # Execute with SSE streaming
        full_response = ""
        async for sse_event in self._executor.execute(
            content, user, str(agent_session.id), skill, analysis_only,
        ):
            lines = sse_event.strip().split("\n")
            if len(lines) >= 2:
                data_str = lines[1].replace("data: ", "")
                try:
                    data = json.loads(data_str)
                    # Collect text content for saving
                    if "content" in data:
                        full_response += data.get("content", "") + " "
                    # Record tool calls to DB
                    if lines[0] == "event: tool_call":
                        await self._tools.create({
                            "session_id": agent_session.id,
                            "step_number": data.get("step", 1),
                            "tool_name": data.get("tool", "unknown"),
                            "input_params": data.get("input", {}),
                            "status": "success",
                        })
                        await self._agent.update(agent_session, {
                            "message_count": agent_session.message_count + 1,
                        })
                    # Record LLM costs from complete event
                    if lines[0] == "event: complete":
                        await self._agent.update(agent_session, {
                            "status": "completed",
                            "ended_at": datetime.now(timezone.utc),
                            "total_cost": data.get("total_cost", 0.0),
                        })
                except (json.JSONDecodeError, KeyError):
                    pass
            yield sse_event

        # Save assistant message
        if full_response.strip():
            await self._msgs.create({
                "session_id": session_id, "role": "assistant",
                "content": full_response.strip(), "sequence": seq + 1,
            })
            await self._chat.update(chat, {
                "message_count": chat.message_count + 2,
                "last_message_at": datetime.now(timezone.utc),
            })

    async def get_session(self, session_id: uuid.UUID, user_id: str = "") -> dict | None:
        obj = await self._chat.get(session_id)
        if obj and user_id and obj.user_id != user_id:
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError("Access denied: session does not belong to you")
        return self._chat_to_dict(obj) if obj else None

    async def list_sessions(self, user_id: str, page: int = 1, page_size: int = 20) -> tuple[int, list[dict]]:
        total, rows = await self._chat.list_by_user(user_id, page, page_size)
        return total, [self._chat_to_dict(r) for r in rows]

    async def delete_session(self, session_id: uuid.UUID, user_id: str = ""):
        obj = await self._chat.get(session_id)
        if obj:
            if user_id and obj.user_id != user_id:
                from app.core.exceptions import ForbiddenError
                raise ForbiddenError("Access denied: session does not belong to you")
            await self._chat.delete(obj)

    async def get_messages(self, session_id: uuid.UUID, user_id: str = "") -> list[dict]:
        # Verify ownership first
        chat = await self._chat.get(session_id)
        if chat and user_id and chat.user_id != user_id:
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError("Access denied: session does not belong to you")
        rows = await self._msgs.list_by_session(session_id)
        return [self._msg_to_dict(r) for r in rows]

    async def get_audit_trail(self, session_id: uuid.UUID) -> dict:
        agent = await self._agent.get(session_id)
        if not agent:
            return {}
        return {
            "session": self._agent_to_dict(agent),
            "preflight_logs": [self._pf_to_dict(r) for r in await self._preflight.list_by_session(session_id)],
            "tool_calls": [self._tc_to_dict(r) for r in await self._tools.list_by_session(session_id)],
            "llm_calls": [self._lc_to_dict(r) for r in await self._llm.list_by_session(session_id)],
            "pending_actions": [self._pa_to_dict(r) for r in await self._pending.list_by_session(session_id)],
        }

    async def confirm_action(self, action_id: uuid.UUID, user_id: str):
        pm = PendingActionManager()
        await pm.approve(str(action_id), user_id)

    async def reject_action(self, action_id: uuid.UUID, user_id: str, reason: str = ""):
        pm = PendingActionManager()
        await pm.reject(str(action_id), user_id, reason)

    async def get_suggestions(self, page: str) -> list[str]:
        for key in SUGGESTIONS_MAP:
            if page.startswith(key):
                return SUGGESTIONS_MAP[key]
        return SUGGESTIONS_MAP["default"]

    def _sse_error(self, msg: str) -> str:
        return f"event: error\ndata: {json.dumps({'message': msg})}\n\n"

    def _chat_to_dict(self, obj) -> dict:
        return {"id": obj.id, "user_id": obj.user_id, "title": obj.title,
                "agent_session_id": obj.agent_session_id, "context_page": obj.context_page,
                "message_count": obj.message_count, "last_message_at": obj.last_message_at,
                "created_at": obj.created_at, "updated_at": obj.updated_at}

    def _msg_to_dict(self, obj) -> dict:
        return {"id": obj.id, "session_id": obj.session_id, "role": obj.role,
                "content": obj.content, "card_type": obj.card_type, "card_data": obj.card_data,
                "sequence": obj.sequence, "created_at": obj.created_at}

    def _agent_to_dict(self, obj) -> dict:
        return {"id": obj.id, "user_id": obj.user_id, "title": obj.title,
                "mode": obj.mode, "skill_id": obj.skill_id, "status": obj.status,
                "total_tokens": obj.total_tokens, "total_cost": obj.total_cost,
                "started_at": obj.started_at, "ended_at": obj.ended_at}

    def _tc_to_dict(self, obj) -> dict:
        return {"id": obj.id, "session_id": obj.session_id, "step_number": obj.step_number,
                "tool_name": obj.tool_name, "input_params": obj.input_params,
                "output_summary": obj.output_summary, "latency_ms": obj.latency_ms,
                "status": obj.status}

    def _lc_to_dict(self, obj) -> dict:
        return {"id": obj.id, "session_id": obj.session_id, "model_name": obj.model_name,
                "prompt_tokens": obj.prompt_tokens, "completion_tokens": obj.completion_tokens,
                "total_cost": obj.total_cost, "latency_ms": obj.latency_ms}

    def _pf_to_dict(self, obj) -> dict:
        return {"id": obj.id, "check_type": obj.check_type, "passed": obj.passed, "detail": obj.detail}

    def _pa_to_dict(self, obj) -> dict:
        return {"id": obj.id, "tool_name": obj.tool_name, "risk_level": obj.risk_level,
                "status": obj.status, "expires_at": obj.expires_at}


class SkillService(ISkillService):
    def __init__(self, skill_repo: SkillRepository):
        self._repo = skill_repo

    async def get_skill(self, skill_id: str) -> dict | None:
        obj = await self._repo.get_by_skill_id(skill_id)
        return self._to_dict(obj) if obj else None

    async def list_skills(self, category: str | None = None) -> list[dict]:
        rows = await self._repo.list_all(category)
        return [self._to_dict(r) for r in rows]

    async def update_skill(self, skill_id: str, data: dict) -> dict:
        obj = await self._repo.get_by_skill_id(skill_id)
        if obj:
            obj = await self._repo.ensure_skill({"skill_id": skill_id, **data})
        return self._to_dict(obj) if obj else {}

    async def ensure_builtin_skills(self):
        from app.modules.module8_ai.capabilities import BUILTIN_SKILLS
        for skill_data in BUILTIN_SKILLS:
            await self._repo.ensure_skill(skill_data)

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "skill_id": obj.skill_id, "name": obj.name,
            "description": obj.description, "category": obj.category,
            "prompt_template": obj.prompt_template, "output_schema": obj.output_schema,
            "allowed_tools": obj.allowed_tools, "risk_level": obj.risk_level,
            "module_dependencies": obj.module_dependencies,
            "is_builtin": obj.is_builtin, "is_enabled": obj.is_enabled,
            "version": obj.version, "created_at": obj.created_at, "updated_at": obj.updated_at,
        }
