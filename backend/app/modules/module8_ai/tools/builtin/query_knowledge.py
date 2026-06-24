"""Built-in tool: query_knowledge — mock implementation."""
from app.modules.module8_ai.tools.base import BaseTool, ToolSpec

MOCK_ARTICLES = [
    {"id": "k1", "title": "OSPF 邻居震荡排查指南", "type": "case",
     "tags": ["OSPF", "路由协议", "Cisco"],
     "summary": "OSPF 邻居状态在 FULL 和 DOWN 之间反复切换，导致路由重新计算、CPU 飙升。"},
    {"id": "k2", "title": "MySQL 慢查询优化手册", "type": "case",
     "tags": ["MySQL", "慢查询", "索引优化"],
     "summary": "数据库查询耗时超过 1 秒，导致应用接口响应延迟。建议检查索引和全表扫描。"},
    {"id": "k3", "title": "交换机光模块故障处理预案", "type": "emergency",
     "tags": ["光模块", "交换机", "链路故障"],
     "summary": "接口光功率低于接收灵敏度下限或 CRC 错误持续增长时的应急处置步骤。"},
    {"id": "k4", "title": "Cisco IOS 配置备份命令模板", "type": "template",
     "tags": ["Cisco", "配置备份"],
     "summary": "Cisco IOS 设备的 running-config 备份命令集合。"},
    {"id": "k6", "title": "支付系统故障应急预案", "type": "emergency",
     "tags": ["支付", "应急预案", "P0"],
     "summary": "支付系统故障的应急响应流程：确认范围、检查依赖、切换备用、数据核对。"},
]


class QueryKnowledgeTool(BaseTool):
    spec = ToolSpec(
        tool_id="query_knowledge",
        name="Query Knowledge Base",
        description="Search the knowledge base for articles, runbooks, templates, "
                    "and emergency plans. Returns relevant articles with summaries.",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword"},
                "article_type": {"type": "string", "description": "case, template, emergency, faq"},
                "tag": {"type": "string", "description": "Filter by tag"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
            },
        },
        required_permissions=["knowledge:article:list"],
        risk_level="read_only",
        timeout_seconds=10,
        module="module7_knowledge",
    )

    async def execute(self, **kwargs) -> dict:
        keyword = kwargs.get("keyword", "").lower()
        article_type = kwargs.get("article_type", "")
        tag = kwargs.get("tag", "")
        limit = kwargs.get("limit", 5)

        results = MOCK_ARTICLES
        if keyword:
            results = [
                a for a in results
                if keyword in a["title"].lower() or keyword in a.get("summary", "").lower()
                or any(keyword in t.lower() for t in a.get("tags", []))
            ]
        if article_type:
            results = [a for a in results if a["type"] == article_type]
        if tag:
            results = [a for a in results if tag in a.get("tags", [])]

        return {
            "found": len(results),
            "articles": results[:limit],
        }
