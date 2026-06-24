"""Tool base classes — ToolSpec metadata + BaseTool ABC."""
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolSpec(BaseModel):
    """Metadata describing a tool the agent can call."""

    tool_id: str                    # "query_device"
    name: str                       # Human-readable name
    description: str                # LLM-facing tool description
    parameters: dict = {}           # JSON Schema for tool input
    required_permissions: list[str] = []  # Permission codes needed
    required_mcp_services: list[str] = []  # External MCP dependencies
    risk_level: str = "read_only"   # read_only | write_safe | write_dangerous
    rollback_tool_id: str | None = None
    timeout_seconds: int = 30
    module: str = "module8_ai"


class BaseTool(ABC):
    """Abstract base for all agent-callable tools.

    Each module registers its tools by subclassing BaseTool
    and implementing execute() with real service calls.
    """

    spec: ToolSpec

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with the given parameters.

        Returns a dict that will be summarized and shown to the LLM.
        """
        ...
