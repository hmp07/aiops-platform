"""Skill: alert_triage — AIOps alert triage and root cause analysis."""

ALERT_TRIAGE_SKILL = {
    "skill_id": "alert_triage",
    "name": "告警分诊与根因分析",
    "description": "分析告警上下文、收集多维证据、推断最可能根因并给出置信度排序",
    "category": "diagnosis",
    "risk_level": "read_only",
    "allowed_tools": ["query_device", "query_alert", "query_knowledge"],
    "module_dependencies": ["module1_asset", "module3_monitoring", "module7_knowledge"],
    "prompt_template": """You are an AIOps alert triage specialist. Given the following alert context, analyze the root cause.

## Alert Context
$context

## Available Data
$data

## Instructions
1. Analyze the alert severity, affected device/service, and time window
2. Use query_device to get device details (manufacturer, model, current status, recent changes)
3. Use query_alert to find related alerts on the same device or neighboring devices
4. Use query_knowledge to find similar historical cases and known solutions
5. Rank possible root causes by probability, citing specific evidence for each
6. Provide actionable remediation steps

## Output Format
- conclusion: Brief summary of the most likely root cause
- confidence: Float 0.0-1.0
- evidence_chain: Array of {source, finding} objects
- hypotheses: Array of {rank, cause, probability, supporting_evidence[], contradicting_evidence[]}
- suggestions: Array of actionable remediation steps
- related_knowledge: Array of relevant KB article references""",
    "output_schema": {
        "type": "object",
        "properties": {
            "conclusion": {"type": "string"},
            "confidence": {"type": "number"},
            "evidence_chain": {"type": "array"},
            "hypotheses": {"type": "array"},
            "suggestions": {"type": "array"},
            "related_knowledge": {"type": "array"},
        },
    },
}
