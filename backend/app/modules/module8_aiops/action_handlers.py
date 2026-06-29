"""M8 AIOps — Action Handlers (sxdevops architecture, FastAPI adaptation).

Maps page context + user question keywords to specific AIOps actions.
Porting from: sxdevops/backend/aiops/action_handlers.py
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

TEXT_LIMIT = 180
LIST_LIMIT = 8


def _clean_text(value: Any, limit: int = TEXT_LIMIT) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = " ".join(text.split())
    return text[:limit]


def _clean_mapping(value: Any, limit: int = 20) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    cleaned = {}
    for key, item in value.items():
        name = _clean_text(key, 64)
        if not name:
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            cleaned[name] = _clean_text(item, TEXT_LIMIT) if isinstance(item, str) else item
        elif isinstance(item, list):
            cleaned[name] = [
                _clean_text(entry, 80)
                for entry in item[:LIST_LIMIT]
                if _clean_text(entry, 80)
            ]
        if len(cleaned) >= limit:
            break
    return cleaned


def _clean_string_list(values: Any, limit: int = LIST_LIMIT) -> List[str]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        text = _clean_text(value, 120)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _first_mapping_value(mapping: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, list):
            value = value[0] if value else ""
        text = _clean_text(value)
        if text:
            return text
    return ""


def normalize_page_context(value: Any) -> Dict[str, Any]:
    """Normalize and clean page context from frontend (sxdevops pattern)."""
    if not isinstance(value, dict):
        return {}

    params = _clean_mapping(value.get("params"))
    query = _clean_mapping(value.get("query"))
    raw_hints = _clean_mapping(value.get("hints"))
    hints = dict(raw_hints)

    inferred = {
        "environment": _first_mapping_value(
            {**params, **query, **raw_hints},
            ["environment", "env", "env_name", "knowledge_environment"],
        ),
        "service": _first_mapping_value(
            {**params, **query, **raw_hints},
            ["service", "service_name", "app", "application", "system", "workload"],
        ),
        "device_id": _first_mapping_value(
            {**params, **query, **raw_hints},
            ["device_id", "deviceId", "id"],
        ),
        "alert_id": _first_mapping_value(
            {**params, **query, **raw_hints},
            ["alert_id", "alertId", "id"],
        ),
        "datasource_type": _first_mapping_value(
            {**params, **query, **raw_hints},
            ["datasource_type", "datasourceType", "ds_type"],
        ),
    }
    for key, text in inferred.items():
        if text and not hints.get(key):
            hints[key] = text

    page = _clean_text(value.get("page") or value.get("name"), 80)
    route = _clean_text(value.get("route") or value.get("path"), 180)
    title = _clean_text(value.get("title"), 80)
    normalized = {
        "page": page,
        "title": title,
        "route": route,
        "params": params,
        "query": query,
        "hints": hints,
        "suggested_questions": _clean_string_list(value.get("suggested_questions")),
    }
    return {key: item for key, item in normalized.items() if item not in ("", {}, [])}


def page_context_value(page_context: Dict[str, Any], name: str) -> str:
    """Extract a specific value from normalized page context."""
    context = normalize_page_context(page_context)
    hints = context.get("hints") if isinstance(context.get("hints"), dict) else {}
    aliases = {
        "environment": ["environment", "env", "knowledge_environment"],
        "service": ["service", "service_name", "app", "application", "system"],
        "device": ["device_id", "deviceId", "id"],
        "alert": ["alert_id", "alertId", "fingerprint"],
        "incident": ["incident", "alert_id", "alertId", "service", "service_name"],
    }
    return _first_mapping_value(hints, aliases.get(name, [name]))


def _route_matches(page_context: Dict[str, Any], prefixes: Iterable[str]) -> bool:
    context = normalize_page_context(page_context)
    route = str(context.get("route") or "").lower()
    page = str(context.get("page") or "").lower()
    return any(
        route.startswith(prefix.lower()) or page.startswith(prefix.lower().strip("/").replace("/", "."))
        for prefix in prefixes
    )


def _question_has_any(question: str, keywords: Iterable[str]) -> bool:
    lowered = str(question or "").lower()
    return any(keyword.lower() in lowered for keyword in keywords if keyword)


def _question_is_context_followup(question: str) -> bool:
    lowered = str(question or "").strip().lower()
    if not lowered:
        return False
    return len(lowered) <= 28 or _question_has_any(
        lowered,
        ["分析一下", "看看", "查一下", "为什么", "有异常吗", "生成一下", "帮我"],
    )


@dataclass(frozen=True)
class ActionHandler:
    """Maps a page route prefix + user question keywords to an action code."""

    code: str
    page_prefixes: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    prompt_hint: str = ""

    def matches_page_context(self, question: str, page_context: Dict[str, Any]) -> bool:
        if not self.page_prefixes or not _route_matches(page_context, self.page_prefixes):
            return False
        if _question_has_any(question, self.keywords):
            return True
        return _question_is_context_followup(question)


# ── Handler Registry (adapted for AIOps-Platform routes) ─────

HANDLERS: Dict[str, ActionHandler] = {
    "device.query": ActionHandler(
        code="device.query",
        page_prefixes=["/asset", "/ipam"],
        keywords=["设备", "device", "server", "服务器", "switch", "router", "资产", "IP", "子网", "subnet"],
        prompt_hint="设备和IPAM页面上下文优先作为设备ID、IP地址和子网的候选输入。",
    ),
    "alert.root_cause": ActionHandler(
        code="alert.root_cause",
        page_prefixes=["/monitoring/alerts"],
        keywords=["告警", "根因", "原因", "影响", "处理", "异常", "alert", "报警"],
        prompt_hint="告警页面上下文优先作为告警ID、严重级别和时间范围的候选输入。",
    ),
    "log.analyze": ActionHandler(
        code="log.analyze",
        page_prefixes=["/log"],
        keywords=["日志", "log", "error", "warn", "查询", "错误", "分析"],
        prompt_hint="日志页面上下文优先作为服务、数据源、日志级别和时间窗口的候选输入。",
    ),
    "topology.analyze": ActionHandler(
        code="topology.analyze",
        page_prefixes=["/apm/topology", "/apm/services"],
        keywords=["拓扑", "topology", "依赖", "dependency", "服务", "service", "调用链"],
        prompt_hint="APM页面上下文优先作为服务名称和依赖关系的候选输入。",
    ),
    "knowledge.search": ActionHandler(
        code="knowledge.search",
        page_prefixes=["/knowledge"],
        keywords=["知识", "knowledge", "sop", "runbook", "文档", "预案"],
        prompt_hint="知识库页面上下文优先作为文章类型和标签的候选输入。",
    ),
    "config.review": ActionHandler(
        code="config.review",
        page_prefixes=["/config"],
        keywords=["配置", "config", "变更", "备份", "版本"],
        prompt_hint="配置页面上下文优先作为设备ID和配置类型的候选输入。",
    ),
}


def select_action_by_handler(
    question: str,
    actions_by_code: Dict[str, Dict[str, Any]],
    page_context: Optional[Dict[str, Any]] = None,
    current_code: str = "",
) -> Optional[Dict[str, Any]]:
    """Select the best action based on page context and question keywords."""
    if current_code and current_code in actions_by_code:
        return actions_by_code[current_code]
    context = normalize_page_context(page_context)
    if not context:
        return None
    for handler in HANDLERS.values():
        action = actions_by_code.get(handler.code)
        if action and handler.matches_page_context(question, context):
            return action
    return None


def handler_for_action(code: str) -> Optional[ActionHandler]:
    return HANDLERS.get(code)


def build_page_context_summary_block(
    page_context: Dict[str, Any],
    action: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Build a structured summary block of the page context."""
    context = normalize_page_context(page_context)
    if not context:
        return None
    hints = context.get("hints") if isinstance(context.get("hints"), dict) else {}
    metrics = []
    for label, key in [("页面", "title"), ("路径", "route")]:
        value = context.get(key)
        if value:
            metrics.append({"label": label, "value": value})
    if action:
        metrics.append(
            {"label": "Action", "value": action.get("display_name") or action.get("code") or "--"}
        )

    items = []
    hint_labels = {
        "environment": "环境",
        "service": "服务/应用",
        "device_id": "设备 ID",
        "alert_id": "告警 ID",
        "datasource_type": "数据源类型",
    }
    for key, label in hint_labels.items():
        value = _clean_text(hints.get(key))
        if value:
            items.append({"label": label, "value": value, "text": f"{label}：{value}"})
    if not metrics and not items:
        return None

    return {
        "id": "page-context",
        "type": "context_summary",
        "title": "页面上下文",
        "summary": "已带入当前页面的环境、资源或筛选条件作为分析线索。",
        "metrics": metrics[:4],
        "items": items[:8],
        "actions": [],
    }


def build_context_form_block(
    action: Dict[str, Any],
    missing_fields: List[Dict[str, Any]],
    page_context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a context form for actions requiring missing info."""
    context = normalize_page_context(page_context)
    fields = []
    items = []
    for item in missing_fields or []:
        if not isinstance(item, dict):
            item = {"name": str(item or ""), "label": str(item or "")}
        name = _clean_text(item.get("name"), 64)
        label = _clean_text(item.get("label") or name, 80) or "上下文"
        suggestion = _clean_text(item.get("suggestion") or item.get("detail"), 160)
        value = page_context_value(context, name)
        field = {
            "name": name,
            "label": label,
            "type": "text",
            "required": True,
            "value": value,
            "placeholder": suggestion or f"请补充{label}",
        }
        fields.append(field)
        items.append({
            "label": label,
            "value": value or "待补充",
            "detail": suggestion or f"请补充{label}后继续。",
            "text": f"{label}：{value or '待补充'}",
            "status": "success" if value else "pending",
        })

    actions = [
        {"type": "reuse", "label": _clean_text(text, 18) or "带上下文继续", "value": text}
        for text in (suggestions or [])[:4]
        if _clean_text(text)
    ]
    if not actions:
        actions = [{"type": "copy", "label": "复制提示", "value": "请补充上下文后继续"}]

    return {
        "id": f"context-form-{action.get('code') or 'action'}",
        "type": "context_form",
        "title": f"{action.get('display_name') or action.get('code') or 'Action'} 预检",
        "summary": "请确认或补充必要上下文后继续，页面上下文只作为候选线索。",
        "status": "needs_info",
        "status_display": "待补充",
        "risk_level": action.get("risk_level") or "read_only",
        "metrics": [
            {"label": "缺失项", "value": f"{len(fields)} 项"},
            {"label": "动作模式", "value": action.get("agent_mode_display") or action.get("agent_mode") or "--"},
            {"label": "风险等级", "value": action.get("risk_level_display") or action.get("risk_level") or "--"},
        ],
        "fields": fields,
        "items": items,
        "actions": actions,
    }


def build_prompt_hint_lines(
    action: Optional[Dict[str, Any]],
    page_context: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Build prompt hint lines for the LLM system prompt."""
    context = normalize_page_context(page_context)
    if not action or not context:
        return []
    handler = handler_for_action(action.get("code") or "")
    lines = []
    if handler and handler.prompt_hint:
        lines.append(f"- {handler.prompt_hint}")
    hints = context.get("hints") if isinstance(context.get("hints"), dict) else {}
    hint_parts = []
    for key in ["environment", "service", "device_id", "alert_id", "datasource_type"]:
        value = _clean_text(hints.get(key), 100)
        if value:
            hint_parts.append(f"{key}={value}")
    if hint_parts:
        lines.append(f"- 当前页面上下文候选：{'; '.join(hint_parts)}")
    return lines
