"""Skill: config_risk_analysis — network configuration change risk assessment."""

CONFIG_RISK_SKILL = {
    "skill_id": "config_risk_analysis",
    "name": "配置变更风险分析",
    "description": "接收配置差异结果，结合变更窗口、历史告警、知识库判断变更风险等级",
    "category": "advisory",
    "risk_level": "read_only",
    "allowed_tools": ["query_device", "query_knowledge"],
    "module_dependencies": ["module5_config", "module7_knowledge"],
    "prompt_template": """You are a network configuration auditor. Analyze this config diff and assess risk.

## Config Diff Context
$context

## Instructions
1. Identify what changed: added, removed, or modified lines
2. Check if the change is in an approved change window
3. Correlate with recent alerts on the affected device
4. Check knowledge base for known risks with similar changes
5. Assign a risk level: normal (routine change in window), suspicious (out of window but low impact), high (out of window, high impact, or matches known dangerous pattern)
6. Provide clear reasoning and rollback guidance

## Output Format
- risk_level: "normal" | "suspicious" | "high"
- reasons: Array of specific reasons for the risk rating
- affected_services: Array of potentially impacted services
- rollback_steps: Array of steps to revert the change
- suggestion: Recommended action""",
    "output_schema": {
        "type": "object",
        "properties": {
            "risk_level": {"type": "string", "enum": ["normal", "suspicious", "high"]},
            "reasons": {"type": "array"},
            "affected_services": {"type": "array"},
            "rollback_steps": {"type": "array"},
            "suggestion": {"type": "string"},
        },
    },
}
