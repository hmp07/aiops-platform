"""Action Router — keyword/rule-based task classification (V1).

V2: Upgrade to lightweight LLM classifier when sufficient session data exists.
"""
import re
from typing import Any


# (rule_type, patterns, mode, intent)
ROUTING_RULES: list[tuple[str, list[str], str, str | None]] = [
    # Direct queries — deterministic, no LLM loop needed
    ("keyword", ["show", "list", "get", "what is", "how many", "query",
                  "display", "find", "search", "lookup", "retrieve"], "direct", None),
    # Analysis — single-threaded ReAct
    ("keyword", ["why", "analyze", "compare", "check", "investigate",
                  "explain", "tell me about", "what caused", "reason"], "react", None),
    # Complex diagnosis — Plan + ReAct
    ("keyword", ["diagnose", "troubleshoot", "root cause", "what happened",
                  "incident", "outage", "failure analysis"], "plan_react", None),
]

# Intent patterns for common deterministic queries
INTENT_PATTERNS: list[tuple[str, str]] = [
    (r"device\s+\S+|show\s+device|list\s+device", "query_device"),
    (r"alert|alarm|告警|warning|critical", "query_alert"),
    (r"knowledge|kb|article|案例|文档|runbook", "query_knowledge"),
    (r"config|配置|backup|备份|diff", "query_config"),
    (r"service|服务|apm|latency|延迟|throughput", "query_service"),
    (r"inspection|巡检|report|报告", "inspection_report"),
]


class ActionRouter:
    """Classifies user input into mode + intent using keyword/pattern rules.

    Usage:
        router = ActionRouter()
        result = router.classify("why is CORE-SW-01 CPU so high?")
        # {"mode": "react", "intent": "query_alert", "confidence": 0.8}
    """

    def classify(self, user_input: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Classify user input and return routing decision.

        Args:
            user_input: The user's raw text input.
            context: Optional context dict with page/resource info.

        Returns:
            {"mode": "direct|react|plan_react", "intent": "query_device|...|None",
             "confidence": 0.0-1.0}
        """
        text_lower = user_input.lower().strip()

        # Step 1: Check intent patterns (exact/close match → high confidence)
        for pattern, intent in INTENT_PATTERNS:
            if re.search(pattern, text_lower):
                # Find what mode this intent maps to
                mode = self._intent_mode(intent)
                return {"mode": mode, "intent": intent, "confidence": 0.85}

        # Step 2: Check routing keywords (partial match → medium confidence)
        scores: dict[str, float] = {}
        for rule_type, patterns, mode, _ in ROUTING_RULES:
            for pat in patterns:
                if pat in text_lower:
                    scores[mode] = scores.get(mode, 0) + 0.15

        if scores:
            best_mode = max(scores, key=scores.get)
            confidence = min(scores[best_mode], 0.75)
            return {"mode": best_mode, "intent": None, "confidence": confidence}

        # Step 3: Heuristics
        if "?" in user_input and not any(w in text_lower for w in ["why", "how", "analyze", "cause"]):
            return {"mode": "direct", "intent": None, "confidence": 0.6}

        if any(w in text_lower for w in ["analyze", "why", "root cause", "cause"]):
            return {"mode": "react", "intent": None, "confidence": 0.7}

        if any(w in text_lower for w in ["diagnose", "investigate", "troubleshoot"]):
            return {"mode": "plan_react", "intent": None, "confidence": 0.7}

        # Step 4: Default → ReAct
        return {"mode": "react", "intent": None, "confidence": 0.5}

    def _intent_mode(self, intent: str) -> str:
        """Map intent to default execution mode."""
        query_intents = {"query_device", "query_alert", "query_config",
                         "query_service", "query_knowledge"}
        report_intents = {"inspection_report"}

        if intent in query_intents:
            return "direct"
        if intent in report_intents:
            return "react"
        return "react"
