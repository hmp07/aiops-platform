"""Agent Executor — LangChain AgentExecutor wrapper with audit trail.

Orchestrates: Route → Preflight → (Direct|ReAct|Plan+ReAct) → Audit.
Yields SSE events at each step for real-time frontend streaming.
"""
import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.modules.module8_ai.agent.action_router import ActionRouter
from app.modules.module8_ai.agent.pending_action import PendingActionManager
from app.modules.module8_ai.agent.preflight import PreflightEngine
from app.modules.module8_ai.llm.client import LLMClient
from app.modules.module8_ai.tools.registry import ToolRegistry


class AgentExecutor:
    """Wraps LangChain AgentExecutor with custom audit pipeline."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        tool_registry: ToolRegistry | None = None,
        preflight_engine: PreflightEngine | None = None,
        pending_manager: PendingActionManager | None = None,
    ):
        self._llm = llm_client or LLMClient()
        self._tools = tool_registry or ToolRegistry.get_instance()
        self._preflight = preflight_engine or PreflightEngine()
        self._pending = pending_manager or PendingActionManager()
        self._router = ActionRouter()
        self._audit: dict[str, Any] = {}

    async def execute(
        self,
        user_input: str,
        user: dict[str, Any],
        session_id: str = "",
        skill: Any = None,
        analysis_only: bool = False,
    ) -> AsyncIterator[str]:
        """Main execution flow. Yields SSE-formatted event strings.

        Yields:
            SSE event strings: "event: {name}\ndata: {json}\n\n"
        """
        session_id = session_id or str(uuid.uuid4())
        self._audit = {"session_id": session_id, "steps": [], "tool_calls": 0, "llm_calls": 0}

        try:
            # Step 1: Route
            route = self._router.classify(user_input)
            yield self._sse("route", {"mode": route["mode"], "intent": route["intent"],
                                       "confidence": route["confidence"]})
            self._audit["mode"] = route["mode"]

            # Step 2: Preflight
            skill_tools = skill.allowed_tools if skill else None
            risk = skill.risk_level if skill else "read_only"
            active_tools = self._tools.get_tools_for_skill(
                skill_allowed_tools=skill_tools,
                user=user,
                risk_limit="write_dangerous" if not analysis_only else "read_only",
            )

            preflight_results = await self._preflight.check(
                user, active_tools, risk, analysis_only,
            )
            yield self._sse("preflight", {
                "permission": "passed" if preflight_results[0].passed else "failed",
                "risk": preflight_results[1].detail.get("effective_risk", "read_only") if len(preflight_results) > 1 else "read_only",
                "needs_approval": preflight_results[1].detail.get("needs_approval", False) if len(preflight_results) > 1 else False,
            })
            self._audit["preflight"] = [{"check": r.check_type, "passed": r.passed, "detail": r.detail} for r in preflight_results]

            # Step 3: Execute by mode
            if route["mode"] == "direct":
                async for event in self._execute_direct(user_input, active_tools, session_id):
                    yield event
            elif route["mode"] == "plan_react":
                async for event in self._execute_react(user_input, active_tools, session_id, plan_first=True):
                    yield event
            else:
                async for event in self._execute_react(user_input, active_tools, session_id):
                    yield event

            # Step 4: Complete
            yield self._sse("complete", {
                "session_id": session_id,
                "total_steps": self._audit["tool_calls"] + self._audit["llm_calls"],
            })

        except Exception as e:
            yield self._sse("error", {"message": str(e), "session_id": session_id})

    async def _execute_direct(
        self, user_input: str, tools: list, session_id: str
    ) -> AsyncIterator[str]:
        """Direct mode: call matching tool, then let LLM format the answer."""
        tool_results: list[dict] = []

        for tool in tools:
            spec = tool.spec
            if spec.tool_id.replace("query_", "") in user_input.lower():
                yield self._sse("thought", {"step": 1, "content": f"Calling {spec.name}..."})
                yield self._sse("tool_call", {"tool": spec.tool_id, "input": {"query": user_input}})
                try:
                    start = time.time()
                    result = await tool.execute(query=user_input)
                    latency = int((time.time() - start) * 1000)
                    summary = str(result)[:800]
                    yield self._sse("tool_result", {"tool": spec.tool_id, "summary": summary, "latency_ms": latency})
                    self._audit["tool_calls"] += 1
                    tool_results.append({"tool": spec.tool_id, "result": result})
                except Exception as e:
                    yield self._sse("error", {"tool": spec.tool_id, "message": str(e)})
                break

        # Let LLM format the answer using tool results
        yield self._sse("thought", {"step": 2, "content": "Generating summary..."})
        context = json.dumps(tool_results, ensure_ascii=False, default=str) if tool_results else "no tool results"
        llm_result = await self._llm.generate([
            {"role": "system", "content": "You are an AIOps assistant. Answer concisely based on tool results."},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": f"Tool results: {context}"},
            {"role": "user", "content": "Provide a concise answer based on the tool results above."},
        ])
        self._audit["llm_calls"] += 1
        yield self._sse("rich_card", {"card_type": "text_response", "data": {"text": llm_result["content"]}})

    async def _execute_react(
        self, user_input: str, tools: list, session_id: str, plan_first: bool = False
    ) -> AsyncIterator[str]:
        """ReAct / Plan+ReAct mode: thought-action-observation loop."""
        max_steps = 10 if not plan_first else 15
        messages = [
            {"role": "system", "content": self._system_prompt(tools)},
            {"role": "user", "content": user_input},
        ]

        if plan_first:
            yield self._sse("thought", {"step": 0, "content": "Planning approach..."})
            self._audit["llm_calls"] += 1

        for step in range(1, max_steps + 1):
            yield self._sse("thought", {"step": step, "content": f"Reasoning step {step}..."})

            # Call LLM with tools
            llm_result = await self._llm.generate(
                messages,
                tools=[t.spec.model_dump() for t in tools],
            )
            self._audit["llm_calls"] += 1
            content = llm_result["content"]

            # Check if LLM wants to call a tool or give final answer
            tool_name = self._extract_tool_call(content, tools)
            if tool_name:
                tool = self._tools.get_tool(tool_name)
                if tool:
                    yield self._sse("tool_call", {"step": step, "tool": tool_name, "input": {}})
                    try:
                        start = time.time()
                        result = await tool.execute()
                        latency = int((time.time() - start) * 1000)
                        summary = str(result)[:500]
                        yield self._sse("tool_result", {"step": step, "tool": tool_name, "summary": summary, "latency_ms": latency})
                        self._audit["steps"].append({"step": step, "tool": tool_name, "status": "success"})
                        self._audit["tool_calls"] += 1
                        messages.append({"role": "assistant", "content": f"Called tool {tool_name}. Result: {summary}"})
                    except Exception as e:
                        yield self._sse("error", {"step": step, "tool": tool_name, "message": str(e)})
                        break
                continue

            # No tool call → final answer
            yield self._sse("rich_card", {
                "card_type": "text_response",
                "data": {"text": content, "steps": step},
            })
            break

    def _system_prompt(self, tools: list) -> str:
        tool_descs = "\n".join(
            f"- {t.spec.tool_id}: {t.spec.description}" for t in tools
        )
        return (
            "You are an AIOps intelligent operations assistant. "
            "Analyze the user's question and use available tools to find the answer.\n\n"
            "Available tools:\n"
            f"{tool_descs}\n\n"
            "When you have enough information, provide a clear answer. "
            "If you need to call a tool, write the tool name in square brackets: [tool_name]"
        )

    def _extract_tool_call(self, content: str, tools: list) -> str | None:
        """Extract tool name from LLM response using [tool_name] pattern."""
        import re
        match = re.search(r'\[(\w+)\]', content)
        if match:
            tool_name = match.group(1)
            for t in tools:
                if t.spec.tool_id == tool_name:
                    return tool_name
        return None

    def _sse(self, event: str, data: dict) -> str:
        """Format an SSE event string."""
        return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
