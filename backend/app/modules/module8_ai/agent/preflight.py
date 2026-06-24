"""Preflight Engine — four-step safety check pipeline.

Checks run in order: Permission → Risk → Dependency → Rollback.
Any FAIL skips subsequent steps.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PreflightResult:
    check_type: str       # permission / risk / dependency / rollback
    passed: bool
    detail: dict[str, Any] = field(default_factory=dict)


class PreflightEngine:
    """Runs 4-step safety checks before any agent execution."""

    RISK_ORDER = {"read_only": 0, "write_safe": 1, "write_dangerous": 2}

    def __init__(self, adapter_registry=None):
        self._adapters = adapter_registry

    async def check(
        self,
        user: dict[str, Any],
        tools: list[Any],
        skill_risk_level: str = "read_only",
        analysis_only: bool = False,
    ) -> list[PreflightResult]:
        """Run the full preflight pipeline.

        Args:
            user: Current user dict (user_id, role).
            tools: List of BaseTool instances the agent will use.
            skill_risk_level: Risk level of the selected skill.
            analysis_only: If True, all write tools are blocked.

        Returns:
            List of PreflightResult, one per check step.
        """
        results: list[PreflightResult] = []

        # Step 1: Permission Check
        perm_result = self._check_permissions(user, tools)
        results.append(perm_result)
        if not perm_result.passed:
            return results

        # Step 2: Risk Assessment
        risk_result = self._check_risk(tools, skill_risk_level, analysis_only)
        results.append(risk_result)

        # Step 3: Dependency Check (stub — no adapters yet)
        dep_result = self._check_dependencies(tools)
        results.append(dep_result)

        # Step 4: Rollback Plan (only for write tools)
        rollback_result = self._check_rollback(tools, skill_risk_level)
        if rollback_result:
            results.append(rollback_result)

        return results

    def _check_permissions(self, user: dict, tools: list) -> PreflightResult:
        """Check if user has required permissions for ALL tools."""
        from app.core.middleware.permissions import has_permission

        failed = []
        for tool in tools:
            spec = tool.spec
            for perm in spec.required_permissions:
                if not has_permission(user, perm):
                    failed.append({"tool": spec.tool_id, "missing_permission": perm})

        if failed:
            return PreflightResult(
                check_type="permission",
                passed=False,
                detail={"failed_tools": failed},
            )
        return PreflightResult(
            check_type="permission",
            passed=True,
            detail={"checked_tools": len(tools), "all_passed": True},
        )

    def _check_risk(
        self, tools: list, skill_risk_level: str, analysis_only: bool
    ) -> PreflightResult:
        """Assess risk level of the operation."""
        max_tool_risk = 0
        write_tools = []

        for tool in tools:
            tool_risk = self.RISK_ORDER.get(tool.spec.risk_level, 0)
            if tool_risk > max_tool_risk:
                max_tool_risk = tool_risk
            if tool_risk > 0:
                write_tools.append(tool.spec.tool_id)

        skill_risk = self.RISK_ORDER.get(skill_risk_level, 0)
        effective_risk = max(max_tool_risk, skill_risk)

        if analysis_only and write_tools:
            return PreflightResult(
                check_type="risk",
                passed=False,
                detail={
                    "effective_risk": "write_dangerous",
                    "write_tools_blocked": write_tools,
                    "reason": "analysis_only mode is enabled",
                },
            )

        risk_label = ["read_only", "write_safe", "write_dangerous"][effective_risk]
        needs_approval = effective_risk >= 2

        return PreflightResult(
            check_type="risk",
            passed=True,
            detail={
                "effective_risk": risk_label,
                "write_tools": write_tools,
                "needs_approval": needs_approval,
                "analysis_only": analysis_only,
            },
        )

    def _check_dependencies(self, tools: list) -> PreflightResult:
        """Check if required external services are reachable.
        Stub implementation — all pass until adapters are implemented.
        """
        services = set()
        for tool in tools:
            for svc in tool.spec.required_mcp_services:
                services.add(svc)

        if not services:
            return PreflightResult(
                check_type="dependency",
                passed=True,
                detail={"status": "no_external_dependencies"},
            )

        # Stub: assume all services available
        return PreflightResult(
            check_type="dependency",
            passed=True,
            detail={"status": "all_available", "services": list(services)},
        )

    def _check_rollback(self, tools: list, skill_risk_level: str) -> PreflightResult | None:
        """Pre-compute rollback plans for write operations."""
        write_tools = [t for t in tools if t.spec.risk_level != "read_only"]
        if not write_tools:
            return None

        plans = {}
        for tool in write_tools:
            if tool.spec.rollback_tool_id:
                plans[tool.spec.tool_id] = {
                    "rollback_tool": tool.spec.rollback_tool_id,
                    "plan": f"Execute rollback tool '{tool.spec.rollback_tool_id}' to revert",
                }
            else:
                plans[tool.spec.tool_id] = {
                    "rollback_tool": None,
                    "plan": "No automatic rollback available. Manual intervention required.",
                }

        all_have_plans = all(p["rollback_tool"] for p in plans.values())
        return PreflightResult(
            check_type="rollback",
            passed=all_have_plans,
            detail={"plans": plans, "all_plans_ready": all_have_plans},
        )
