"""Skill: inspection_report — AI-powered weekly inspection report generation."""

INSPECTION_SKILL = {
    "skill_id": "inspection_report",
    "name": "AI 巡检报告生成",
    "description": "基于采集的性能数据、应用健康度、配置合规状态，自动生成巡检报告",
    "category": "report",
    "risk_level": "read_only",
    "allowed_tools": ["query_device", "query_alert"],
    "module_dependencies": ["module1_asset", "module3_monitoring"],
    "prompt_template": """You are an AIOps inspection report generator. Generate a weekly inspection summary.

## Context
$context

## Instructions
1. Summarize overall device health: total, online, offline, warning
2. Highlight critical alerts that need immediate attention
3. Report on configuration backup status (success/failure count)
4. Report on application service health (SLO compliance)
5. Identify IP address utilization warnings
6. Note any anomaly detection findings
7. Provide focus items for next week

## Output Format
- summary: Markdown-formatted executive summary
- focus_items: Array of {title, severity, description, suggested_action}
- healthy_items: Array of positive findings
- next_week_focus: Array of recommendations for next week
- metrics: {total_devices, online_devices, active_alerts, backup_success_rate, service_health_pct}""",
    "output_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "focus_items": {"type": "array"},
            "healthy_items": {"type": "array"},
            "next_week_focus": {"type": "array"},
            "metrics": {"type": "object"},
        },
    },
}
