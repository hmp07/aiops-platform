"""M8 AI Engine — Abstract Interfaces."""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID


class IToolRegistry(ABC):
    """Central registry for agent-callable tools."""

    @abstractmethod
    def register(self, tool: Any): ...

    @abstractmethod
    def get_tool(self, tool_id: str) -> Any | None: ...

    @abstractmethod
    def list_tools(self) -> list[Any]: ...

    @abstractmethod
    def get_tools_for_skill(self, skill: Any, user: dict) -> list[Any]: ...


class IAgentService(ABC):
    """Core agent dispatch and session management."""

    @abstractmethod
    async def create_session(
        self, user: dict, title: str = "New Chat",
        context_page: str | None = None, context_resource: dict | None = None,
    ) -> dict: ...

    @abstractmethod
    async def send_message(
        self, session_id: UUID, content: str, user: dict,
        skill_id: str | None = None, analysis_only: bool = False,
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    async def get_session(self, session_id: UUID) -> dict | None: ...

    @abstractmethod
    async def list_sessions(self, user_id: str, page: int = 1, page_size: int = 20) -> tuple[int, list[dict]]: ...

    @abstractmethod
    async def delete_session(self, session_id: UUID): ...

    @abstractmethod
    async def get_messages(self, session_id: UUID) -> list[dict]: ...

    @abstractmethod
    async def get_audit_trail(self, session_id: UUID) -> dict: ...

    @abstractmethod
    async def confirm_action(self, action_id: UUID, user_id: str): ...

    @abstractmethod
    async def reject_action(self, action_id: UUID, user_id: str, reason: str = ""): ...

    @abstractmethod
    async def get_suggestions(self, page: str) -> list[str]: ...


class ISkillService(ABC):
    """Skill template management."""

    @abstractmethod
    async def get_skill(self, skill_id: str) -> dict | None: ...

    @abstractmethod
    async def list_skills(self, category: str | None = None) -> list[dict]: ...

    @abstractmethod
    async def update_skill(self, skill_id: str, data: dict) -> dict: ...

    @abstractmethod
    async def ensure_builtin_skills(self): ...
