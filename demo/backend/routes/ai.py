import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from mock_data import ALERTS, INSPECTION_REPORTS

router = APIRouter(tags=["AI"])

AI_RESPONSES = {
    "支付服务最近1小时有异常吗？": "根据 SigNoz APM 数据分析，**支付服务在过去 1 小时内确实存在异常**：\n\n"
        "| 指标 | 当前值 | 基线值 | 状态 |\n"
        "|------|--------|--------|------|\n"
        "| P99 延迟 | 3,500ms | 120ms | 🔴 异常 |\n"
        "| 错误率 | 2.3% | 0.01% | 🔴 异常 |\n"
        "| 吞吐量 | 380 RPS | 850 RPS | 🟡 下降 |\n\n"
        "**AI 根因分析**（跨层定界 H8.10）：\n"
        "- 75% 概率：数据库 orders 表缺失索引，全表扫描 120 万行导致慢查询\n"
        "- 20% 概率：ACC-SW-01 Gi1/0/20 接口 CRC 错误导致 TCP 重传\n"
        "- 5% 概率：支付服务 v3.2.1 发布引入了 N+1 查询\n\n"
        "**建议操作**：\n"
        "1. 立即对 `orders.status` 字段添加索引\n"
        "2. 检查 ORM 生成的 SQL 确认是否存在 N+1 问题\n"
        "3. 检查 ACC-SW-01 Gi1/0/20 接口的光模块状态",

    "CORE-SW-01的CPU为什么这么高？": "**CORE-SW-01 CPU 飙升至 95% 的原因分析**：\n\n"
        "根据告警 a1 的 AI 根因分析（C3.9）：\n\n"
        "| 排名 | 可能原因 | 概率 | 关键证据 |\n"
        "|------|---------|------|--------|\n"
        "| 1 | OSPF 邻居震荡导致路由重算 | 65% | 配置变更记录 + 邻居状态 3 次切换 |\n"
        "| 2 | 二层环路导致广播风暴 | 25% | STP 拓扑变更计数增加 |\n"
        "| 3 | 外部 DDoS 攻击 | 10% | 防火墙流量异常 |\n\n"
        "**关联证据链**：\n"
        "- 2h 前：工程师李运维修改了 OSPF 配置（新增 `no passive-interface Vlan100`）\n"
        "- 5min 后：OSPF 邻居 10.1.1.2 开始状态抖动\n"
        "- 3min 后：CPU 突破 90% 阈值\n\n"
        "**建议**：回滚 OSPF 配置修改，检查 Gi1/0/48 光纤连接状态。",

    "最近有哪些配置变更？": "**最近 24 小时配置变更记录**：\n\n"
        "| 时间 | 设备 | 变更类型 | 操作人 | 风险等级 |\n"
        "|------|------|---------|--------|--------|\n"
        "| 2026-05-28 04:00 | CORE-SW-01 | OSPF 配置修改 | 李运维 | 🔴 高危 |\n"
        "| 2026-05-27 22:00 | CORE-SW-01 | 接口 shutdown | 李运维 | 🔴 高危 |\n"
        "| 2026-05-27 14:00 | AGG-SW-01 | VLAN 添加 | 李运维 | 🟢 正常 |\n\n"
        "⚠️ **注意**：CORE-SW-01 的两项变更均在非变更窗口内执行，且 OSPF 变更已被 AI 判定为可能导致当前告警的根因。",

    "数据库慢查询影响了哪些业务？": "根据 APM Trace 分析，**数据库慢查询主要影响以下业务**：\n\n"
        "| 受影响服务 | 影响程度 | P99 延迟增幅 | 错误率变化 |\n"
        "|-----------|---------|-------------|----------|\n"
        "| 支付服务 | 🔴 严重 | 120→3500ms | 0.01%→2.3% |\n"
        "| 订单服务 | 🟡 轻微 | 80→180ms | 无变化 |\n"
        "| 用户服务 | 🟢 无影响 | 55ms | 无变化 |\n\n"
        "**影响链路**：api-gateway → payment-service → mysql-db（orders 表）\n\n"
        "**根因**：orders 表 status 字段缺失索引，SELECT * FROM orders WHERE status='pending' 全表扫描 120 万行。\n\n"
        "**波及范围**：仅支付服务严重受影响，订单服务因查询不同表而轻微波及。建议优先对 orders.status 创建索引。",

    "当前网络拓扑健康状态怎么样？": "**当前网络拓扑健康状态**：\n\n"
        "| 设备 | 角色 | 健康状态 | 关键指标 |\n"
        "|------|------|---------|--------|\n"
        "| CORE-SW-01 | 核心交换 | 🔴 异常 | CPU 95% |\n"
        "| CORE-SW-02 | 核心交换 | 🟢 正常 | CPU 25% |\n"
        "| AGG-SW-01 | 汇聚交换 | 🟡 警告 | CRC 错误增长 |\n"
        "| AGG-SW-02 | 汇聚交换 | 🟢 正常 | — |\n"
        "| ACC-SW-01 | 接入交换 | 🟡 警告 | 备份失败 |\n"
        "| FW-01 | 防火墙 | 🟢 正常 | 会话 45% |\n"
        "| ROUTER-01 | 出口路由 | 🟢 正常 | 流量 55% |\n\n"
        "**应用层拓扑**：\n"
        "- 支付服务 🔴 异常（P99 3500ms）→ MySQL 🟡 警告（慢查询）\n"
        "- 其他 6 个服务 🟢 正常\n\n"
        "建议优先处理 CORE-SW-01 的 OSPF 问题和支付服务的数据库慢查询。",
}


@router.post("/ai/chat")
async def ai_chat(body: dict):
    question = body.get("question", "")
    answer = AI_RESPONSES.get(question, "抱歉，我无法回答这个问题。请尝试其他问题，或联系运维工程师获取帮助。\n\n您可以尝试询问：\n- 支付服务最近1小时有异常吗？\n- CORE-SW-01的CPU为什么这么高？\n- 最近有哪些配置变更？\n- 数据库慢查询影响了哪些业务？\n- 当前网络拓扑健康状态怎么样？")

    async def stream():
        for word in answer.split():
            yield f"data: {json.dumps({'content': word + ' '})}\n\n"
            await asyncio.sleep(0.03)
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/ai/inspection-reports")
async def list_inspection_reports():
    return {"items": INSPECTION_REPORTS}


@router.get("/ai/inspection-reports/{report_id}")
async def get_inspection_report(report_id: str):
    for r in INSPECTION_REPORTS:
        if r["id"] == report_id:
            return r
    return None


@router.post("/ai/generate-report")
async def generate_report():
    return {"task_id": "report-gen-001", "message": "巡检报告生成已提交，请稍候查看结果"}


@router.get("/ai/root-cause/{alert_id}")
async def get_root_cause(alert_id: str):
    for a in ALERTS:
        if a["id"] == alert_id and a.get("root_cause"):
            return a["root_cause"]
    return {"message": "暂无 AI 根因分析结果"}
