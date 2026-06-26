"""M8 AIOps — Tool Registry (sxdevops pattern).

Central registry for all platform MCP tools. Tools are defined with
name/title/description/input_schema/handler and executed via invoke().
"""

import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

# Handler signature: async def handler(query: str, **kwargs) -> dict
ToolHandler = Callable[..., Coroutine[Any, Any, dict]]


class ToolSpec:
    """Immutable tool definition."""

    __slots__ = (
        "name", "title", "description", "handler_name",
        "input_schema", "permission", "_handler",
    )

    def __init__(
        self,
        name: str,
        title: str,
        description: str,
        handler_name: str,
        input_schema: dict,
        permission: str = "",
        handler: Optional[ToolHandler] = None,
    ):
        self.name = name
        self.title = title
        self.description = description
        self.handler_name = handler_name
        self.input_schema = input_schema
        self.permission = permission
        self._handler = handler

    def bind(self, handler: ToolHandler) -> "ToolSpec":
        """Return a new ToolSpec with handler bound."""
        return ToolSpec(
            name=self.name,
            title=self.title,
            description=self.description,
            handler_name=self.handler_name,
            input_schema=self.input_schema,
            permission=self.permission,
            handler=handler,
        )

    @property
    def handler(self) -> Optional[ToolHandler]:
        return self._handler

    def to_dict(self, user: dict | None = None) -> dict:
        """Serialize to MCP-compatible dict (sxdevops format)."""
        available = True
        if self.permission and user:
            user_perms = user.get("permissions", []) if isinstance(user, dict) else []
            available = self.permission in user_perms if user_perms else True

        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
            },
            "permission": self.permission,
            "available": available,
        }


class ToolRegistry:
    """Singleton registry of all platform MCP tools."""

    _tools: Dict[str, ToolSpec] = {}
    _handlers: Dict[str, ToolHandler] = {}

    @classmethod
    def register(cls, spec: ToolSpec, handler: ToolHandler) -> ToolSpec:
        """Register a tool with its handler function."""
        bound = spec.bind(handler)
        cls._tools[spec.name] = bound
        cls._handlers[spec.handler_name] = handler
        logger.info("Registered MCP tool: %s", spec.name)
        return bound

    @classmethod
    def get(cls, name: str) -> Optional[ToolSpec]:
        return cls._tools.get(name)

    @classmethod
    def get_handler(cls, handler_name: str) -> Optional[ToolHandler]:
        return cls._handlers.get(handler_name)

    @classmethod
    def list_all(cls, user: dict | None = None) -> List[dict]:
        """List all registered tools, filtered by user permissions."""
        return [
            spec.to_dict(user)
            for spec in cls._tools.values()
            if spec.handler is not None
        ]

    @classmethod
    def clear(cls):
        """Clear all registrations (for testing)."""
        cls._tools.clear()
        cls._handlers.clear()


# Convenience exports
register_tool = ToolRegistry.register
get_tool = ToolRegistry.get
get_handler = ToolRegistry.get_handler
list_tools = ToolRegistry.list_all
