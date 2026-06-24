"""ToolRegistry — singleton registry for agent tools with dynamic filtering."""
from typing import Any

from app.core.exceptions import ForbiddenError
from app.modules.module8_ai.tools.base import BaseTool, ToolSpec


class ToolRegistry:
    """Central registry for all agent-callable tools.

    Tools are registered at app startup by each module.
    The registry filters tools per request based on:
      1. Skill's allowed_tools list
      2. User's RBAC permissions
      3. Tool risk level vs Preflight assessment
    """

    _instance: "ToolRegistry | None" = None

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """Register a tool. Called by modules at startup."""
        self._tools[tool.spec.tool_id] = tool

    def get_tool(self, tool_id: str) -> BaseTool | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> list[ToolSpec]:
        """Return all registered tool specs (unfiltered)."""
        return [t.spec for t in self._tools.values()]

    def get_tools_for_skill(
        self,
        skill_allowed_tools: list[str] | None = None,
        user: dict | None = None,
        risk_limit: str = "write_dangerous",
    ) -> list[BaseTool]:
        """Filter tools by Skill constraints × RBAC × Risk.

        Args:
            skill_allowed_tools: Tool IDs the skill allows (None = all).
            user: Current user dict with role info.
            risk_limit: Maximum risk level allowed (read_only < write_safe < write_dangerous).

        Returns:
            List of BaseTool instances that pass all filters.
        """
        RISK_ORDER = {"read_only": 0, "write_safe": 1, "write_dangerous": 2}
        max_risk = RISK_ORDER.get(risk_limit, 2)

        result = []
        for tool in self._tools.values():
            spec = tool.spec

            # Filter 1: Skill allowed tools
            if skill_allowed_tools is not None and spec.tool_id not in skill_allowed_tools:
                continue

            # Filter 2: User RBAC
            if user and spec.required_permissions:
                from app.core.middleware.permissions import has_permission
                if not all(has_permission(user, p) for p in spec.required_permissions):
                    continue

            # Filter 3: Risk level
            tool_risk = RISK_ORDER.get(spec.risk_level, 0)
            if tool_risk > max_risk:
                continue

            result.append(tool)

        return result

    def clear(self):
        """Clear all registered tools (for testing)."""
        self._tools.clear()
