# AIOps Platform 架构设计说明书（V2.0）

---

**版本**：V3.0
**日期**：2026-06-25
**状态**：全部 Phase 1-9 已完成，9/11 模块实现，94 API 路由，35 张表

---

## 一、项目概述

### 1.1 项目定位

AIOps Platform 是一个 AI 增强型智能运维管理平台，借鉴 SxDevOps 开源项目的成熟设计模式，以"受控编排、事件驱动、精细权限、人机协作"为核心理念，打通设备资产、IP 管理、基础设施监控、日志分析、配置管理、应用性能监控、知识库、AI 智能运维、事件墙和调度管理的完整链条。

### 1.2 技术选型

| 层面 | 技术 | 选型理由 |
|------|------|---------|
| 后端框架 | Python FastAPI | 异步高性能、Pydantic 类型安全、原生 async/await |
| 前端框架 | React 19 + TypeScript | 生态丰富、Ant Design 企业级组件、复杂可视化 |
| 关系数据库 | PostgreSQL + TimescaleDB | 时序数据优化、ACID 事务、统一运维 |
| 缓存/消息 | Redis | 会话缓存、Celery Broker、实时状态 |
| 对象存储 | MinIO（S3 兼容） | 配置文件加密存储、版本管理 |
| AI Agent | 自定义编排 + LangChain Executor | 安全关卡自定义，LLM 循环复用 LangChain |
| 任务调度 | Celery | 定时采集、备份、巡检、故障分析 |
| 向量搜索 | pgvector | 知识库 RAG，与业务数据共存 |
| 网络自动化 | Netmiko / PySNMP | 多厂商 SSH、SNMP v2c/v3 |
| 容器化 | Docker Compose | 统一开发/测试/生产环境 |

---

## 二、架构总览

### 2.1 11 模块架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend (React 19 + TypeScript)                │
│         Ant Design 5 + ECharts + ReactFlow + Monaco Editor          │
│    26 routes / 17 pages / FAB AI Chat Widget / Rich Card System    │
├─────────────────────────────────────────────────────────────────────┤
│                      API Layer (FastAPI)                             │
│   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│   │ M1   │ │ M2   │ │ M3   │ │ M4   │ │ M5   │ │ M6   │          │
│   │Asset │ │IPAM  │ │Monit │ │Log   │ │Config│ │APM   │          │
│   └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘          │
│      │        │        │        │        │        │               │
│   ┌──┴────────┴────────┴────────┴────────┴────────┴──┐            │
│   │                  EventWall (M10)                   │            │
│   │          统一事件总线 / 故障分析 / 审计追溯          │            │
│   └──────────────────────┬───────────────────────────┘            │
│   ┌──────┐ ┌──────┐ ┌────┴─────┐ ┌──────┐                        │
│   │ M7   │ │ M8   │ │ M9       │ │ M11  │                        │
│   │Knowl │ │AI    │ │Platform  │ │Sche  │                        │
│   │edge  │ │Engine│ │+ RBAC    │ │duler │                        │
│   └──────┘ └──────┘ └──────────┘ └──────┘                        │
├─────────────────────────────────────────────────────────────────────┤
│   Integrations: iTop / Zabbix / SigNoz / SSH / SNMP / Webhook     │
├─────────────────────────────────────────────────────────────────────┤
│   Infrastructure: PostgreSQL+TimescaleDB / Redis / MinIO / Celery  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责矩阵

| 模块 | 名称 | 状态 | 核心职责 |
|------|------|------|---------|
| **M1** | 设备资产管理 | ✅ Phase 4 | 设备 CRUD + 校准（10 个 API 端点）、EventRecordingMixin |
| **M2** | IP 地址管理 | ✅ Phase 4 | 子网/VLAN 管理、IP 分配/释放状态机（7 个 API 端点） |
| **M3** | 基础设施监控与告警 | ✅ Phase 5 | 告警状态机（5态）、规则引擎、Webhook、降噪去重、证据收集、通知策略（6 表 14 端点） |
| **M4** | 日志分析 | ✅ Phase 9 | Syslog/API 日志汇聚、TimescaleDB 存储、关键字检索、5 端点 |
| **M5** | 配置备份与自动化 | ✅ Phase 4 | 备份触发、Diff 引擎（difflib）、风险评级（5 个 API 端点） |
| **M6** | 应用性能监控 | ✅ Phase 6 | SigNoz 对接、服务拓扑、跨层数据关联（F6.5/F6.9）、3 表 7 端点 |
| **M7** | 知识库 | ✅ Phase 7 | 文章管理、全文搜索、pgvector 嵌入、G7.9 自动归档、知识图谱（邻接表） |
| **M8** | AI 智能引擎 | 待重写 | Action Router、Preflight 安全关卡、Skill/SOP 系统、Tool Registry、两阶段安全、知识图谱 |
| **M9** | 平台基础 + RBAC | Phase 2 已完成 | 用户/角色/权限（90 权限码 + 7 内置角色）、模块可见性、Demo 守卫、审计日志 |
| **M10** | EventWall 事件墙 | Phase 2 已完成 | 统一事件总线（28 字段）、ORM 自动采集、Webhook 接入、故障分析引擎 |
| **M11** | 调度与集成网关 | 待实施 | Celery 任务管理、适配器生命周期、外部系统凭证轮换 |

### 2.3 跨模块通信机制

```
Module A → Module B Interface        [同步查询，立即返回]
Module A → EventWall.publish()       [异步事件，所有模块可订阅]
Agent (M8) → Tool Registry → Module Interface  [工具发现 + 动态调用]
Celery Task → Module Interface       [定时/长任务，通过 EventWall 记录结果]
```

### 2.4 依赖注入规则（核心约束）

模块之间**禁止直接 import 对方的 Service 实现类**。跨模块通信遵循以下规则：

```python
# ✅ 正确：通过抽象接口依赖注入
class EvidenceCollector:
    def __init__(self, log_service: ILogQueryService): ...

# ✅ 正确：通过 EventWall 发布异步事件
await event_service.publish(
    event_type="alert.triggered",
    source_module="module3_monitoring",
    resource_type="alert",
    resource_id=alert_id,
    severity="critical",
    correlation_id=incident_id,
)

# ❌ 错误：直接导入其他模块的具体实现
from app.modules.module4_log.service import LogService
```

---

## 三、EventWall 事件墙（M10）

### 3.1 设计理念

EventWall 是整个平台的**神经中枢**——所有模块的 CRUD 操作、外部事件、Agent 行为都通过统一的 28 字段事件 Schema 汇聚，实现端到端可追溯。

### 3.2 通用事件 Schema

```json
{
  "id": "uuid",
  "event_type": "alert.triggered",
  "event_version": 1,
  "source_module": "module3_monitoring",
  "source_component": "rule_engine",
  "timestamp": "2026-05-29T10:30:00Z",
  "received_at": "2026-05-29T10:30:00Z",
  "producer_type": "system|webhook|user|agent",
  "producer_user_id": null,
  "producer_agent_session_id": null,
  "correlation_id": "uuid-of-business-flow",
  "parent_event_id": null,
  "root_event_id": null,
  "fault_id": null,
  "incident_id": null,
  "resource_type": "alert",
  "resource_id": "a1",
  "resource_name": "CORE-SW-01 CPU 飙升至 95%",
  "resource_module": "module3_monitoring",
  "severity": "critical",
  "status": "new",
  "payload": { },
  "tags": { "env": "production" },
  "metrics": { "duration_ms": 1234 },
  "context_ip_address": "192.168.1.100",
  "context_request_id": null,
  "retention_ttl_days": 90
}
```

### 3.3 自动采集机制（ORM Mixin）

```python
class Device(Base, EventRecordingMixin):
    __event_resource_type__ = "device"
    # CRUD 操作自动发布 device.created / device.updated / device.deleted 事件
```

所有继承 `EventRecordingMixin` 的模型，其 CRUD 操作通过 SQLAlchemy 事件监听器自动记录到 EventWall，模块开发者无需手动调用 `publish()`。

### 3.4 外部 Webhook 接入

```
POST /api/v1/events/webhook/{zabbix|signoz|grafana|jenkins|gitlab|custom}
```

事件源管理支持启用/禁用、Token 鉴权、Schema 转换配置。

### 3.5 故障分析引擎

Celery 每 30 秒运行一次：
1. 滑动窗口 5 分钟 → 读取事件
2. 按 correlation_id / resource_id / 时间邻近分组
3. 严重度加权评分（emergency=10, critical=5, warning=2, info=1）
4. 资源关键度加成（来自 CMDB）
5. 超阈值（≥3 分）集群 → 写入 `fault_wall_events` → 推送通知

### 3.6 存储策略（TimescaleDB）

| 数据类型 | 保留期 | 压缩策略 |
|---------|--------|---------|
| 原始事件 | 90 天 | 7 天后自动压缩（5-10x） |
| 聚合视图 | 365 天 | — |
| 故障集群 | 30 天 | 1 天后压缩 |

---

## 四、Agent 引擎重设计（M8）

### 4.1 三模式 Action Router

```
用户输入 → Action Router（分类）
    ├── Direct Mode（确定性查询，无 LLM 循环）
    │     用于："查询设备 X""列出告警"
    │     流程：preflight → execute → respond
    │
    ├── ReAct Mode（工具编排分析，单线程循环）
    │     用于："分析延迟原因""对比配置风险"
    │     流程：preflight → thought → act → observe → ... → respond
    │
    └── Plan+ReAct Mode（复杂多步规划，两阶段）
          用于："调查支付服务退化全过程"
          流程：preflight → plan → [thought → act → observe]*n → respond
```

### 4.2 Preflight 安全关卡（4 步检查）

```
Input → 权限校验 → 风险评估 → 依赖检查 → 回滚计划
```

| 步骤 | 检查内容 | 失败处理 |
|------|---------|---------|
| 权限 | 用户是否拥有所需全部工具的权限码 | 403 Forbidden |
| 风险 | `read_only` / `write_safe` / `write_dangerous` | 标记并要求确认 |
| 依赖 | 外部系统可达性（SigNoz/Zabbix 健康检查） | 降级模式 + 标注缺口 |
| 回滚 | 写操作预计算回滚方案 | 无回滚 → 拒绝执行 |

### 4.3 Skill/SOP 模板系统

```python
SkillManifest {
    skill_id: str          # "alert_triage", "inspection_report"
    name: str              # 人类可读名称
    allowed_tools: list    # 该 Skill 可调用的工具列表
    prompt_template: str   # Jinja2 模板，{context} + {data}
    output_schema: dict    # JSON Schema 约束输出格式
    risk_level: str        # read_only | write_safe | write_dangerous
    module_dependencies: list  # 依赖的模块接口
}
```

预置 7 个内置 Skill：

| Skill | 用途 | 关联模块 |
|-------|------|---------|
| `alert_triage` | 分析告警上下文、收集证据、建议根因 | M3, M8 |
| `config_risk_analysis` | 评估配置变更风险等级 | M5, M8 |
| `inspection_report` | 生成周度巡检报告 | M1, M3, M6 |
| `cross_layer_diagnosis` | 跨层定界（应用/网络/数据库） | M6, M8 |
| `anomaly_investigation` | 调查日志/指标异常 | M4, M8 |
| `it_change_advisory` | 变更前风险评估 | M5, M7 |
| `knowledge_retrieval` | RAG 知识库检索 | M7 |

### 4.4 工具注册 + 动态过滤

```
Skill.allowed_tools
    → 过滤 MCP 服务器可用性
    → 过滤用户 RBAC 权限码
    → 过滤动作安全等级（Preflight）
    → 最终工具集 → Agent Executor
```

每个模块通过 `ToolRegistry.register()` 注册工具，引擎层只做发现和编排。模块拥有工具定义，AI 模块拥有注册表。

### 4.5 两阶段安全模式

```
只读操作:
  Router → Preflight(read_only) → Direct execution → Format → Return

写入操作:
  Router → Preflight(write, risk_assessed, rollback_computed)
        → 生成 PendingAction 卡片
        → 用户在前端确认
        → 执行 → 记录结果 → Return

自动写入（定时任务、已知安全操作）:
  Router → Preflight(write, pre-authorized) → Execute → Log → Return
```

### 4.6 审计轨迹（5 张表）

| 表 | 记录内容 |
|---|---------|
| `agent_sessions` | 会话元数据、模式、Skill、状态、总 Token、总费用 |
| `agent_tool_calls` | 每次工具调用：名称、参数、结果摘要、延迟、状态 |
| `agent_llm_calls` | 每次 LLM 调用：模型、Token 数、费用（用于成本追踪） |
| `agent_preflight_logs` | 安全检查结果：权限/风险/依赖/回滚 |
| `agent_pending_actions` | 待确认动作：风险等级、超时时间、确认状态 |

### 4.7 LangChain 边界

```
✅ LangChain 负责:
   - AgentExecutor（ReAct 循环引擎）
   - PromptTemplate（Skill 模板渲染）
   - StructuredTool 包装器
   - LLM 调用（ChatAnthropic / ChatOpenAI）

❌ 自定义 Python 负责:
   - Action Router（模式选择）
   - Preflight（安全关卡）
   - 审批门禁（两阶段安全）
   - 审计记录（5 张表）
   - Tool Registry（发现 + 过滤）
   - Skill 生命周期管理
```

---

## 五、RBAC 权限系统（M9）

### 5.1 权限码体系

格式：`{module}:{resource}:{action}`，共 90 个权限码覆盖 10 个业务模块。

| 模块 | 权限码数 | 示例 |
|------|---------|------|
| asset | 10 | `asset:device:list`, `asset:calibration:approve` |
| ipam | 9 | `ipam:subnet:create`, `ipam:ip:allocate` |
| monitoring | 14 | `monitoring:alert:acknowledge`, `monitoring:rule:update` |
| log | 6 | `log:source:create`, `log:entry:search` |
| config | 9 | `config:backup:restore`, `config:batch:execute` |
| apm | 5 | `apm:topology:view`, `apm:trace:view` |
| knowledge | 7 | `knowledge:article:publish`, `knowledge:archive:manage` |
| ai | 12 | `ai:skill:manage`, `ai:action:confirm` |
| eventwall | 5 | `eventwall:fault:list`, `eventwall:source:manage` |
| platform | 13 | `platform:user:create`, `platform:module:manage` |

### 5.2 端点级权限

```python
@router.get("/devices")
@require_permission("asset:device:list")
async def list_devices(...): ...
```

### 5.3 内置角色

| 角色 | code | 权限范围 |
|------|------|---------|
| 超级管理员 | `superadmin` | `*:*:*` |
| 管理员 | `admin` | 全部模块操作（不含平台用户管理） |
| 运维操作员 | `operator` | 运维模块读写（无 delete） |
| 运维工程师 | `engineer` | 标准运维（无 delete/rollback/高危） |
| 只读观察员 | `viewer` | 仅 `list` + `retrieve` + `search` |
| 审计员 | `auditor` | 审计 + 事件只读 |
| 演示账号 | `demo` | 只读 + 中间件强制拦截写操作 |

### 5.4 演示账号保护

```python
# DemoGuardMiddleware: demo 角色 → 非 GET/HEAD/OPTIONS → 直接 403
# 防御纵深：权限码层 + HTTP 中间件层 双重保护
```

---

## 六、前端 AI 对话重设计

### 6.1 双模式

| 模式 | 触发方式 | 说明 |
|------|---------|------|
| **浮窗模式 (FAB)** | 右下角机器人图标 | Ant Design Drawer 弹出，全局可用，上下文感知 |
| **嵌入模式** | `/ai/chat` 路由 | 全屏页面，会话列表侧边栏，完整功能 |

### 6.2 SSE 流式响应

```
POST /api/v1/ai/sessions/{id}/messages → SSE stream
  event: thought       → { step, thought }
  event: tool_call     → { tool, input }
  event: rich_card     → { card_type, data }
  event: pending_action → { action_id, risk, rollback }
  event: complete      → { session_id }
```

备选方案：polling 回退（`?polling=true`）

### 6.3 富响应卡片类型

| 卡片类型 | 说明 | 前端组件 |
|---------|------|---------|
| `context_summary` | 关键信息摘要 | Card + 高亮字段 |
| `evidence_timeline` | 证据时间线 | ECharts Timeline |
| `incident_card` | 告警/事件详情 | Card + 严重度标签 |
| `metric_chart` | 时序指标 | ECharts 折线图 |
| `topology_graph` | 拓扑子图 | ReactFlow 迷你图 |
| `pending_action` | 待确认操作 | Card + 确认/拒绝按钮 |
| `knowledge_suggestion` | 相关知识文章 | List + 相关性评分 |
| `device_list` | 设备表格 | Ant Design Table |
| `text_response` | 纯文本回答 | Markdown 渲染 |

---

## 七、知识图谱（M8 能力）

### 7.1 数据来源

CMDB（设备节点） → LLDP/ARP（实际拓扑边） → APM Trace（服务节点） → 配置（属性附加）

### 7.2 实体与关系

- **实体**：device, interface, service, host, ip_address, subnet, config, alert, incident
- **关系**：has_interface, connected_to, runs_on, assigned_to, belongs_to, affects

### 7.3 存储与更新

- PostgreSQL 邻接表（`graph_nodes` + `graph_edges`）
- 每日全量重建（Celery）+ 事件驱动增量更新
- Redis 查询缓存（30s TTL）+ 物化视图（5min 刷新）

### 7.4 前端可视化

ReactFlow 三种视图：
- **泳道图**：应用层 → 主机层 → 网络层，故障分层定位
- **辐射图**：选中资源居中，N 跳邻居辐射展开，影响分析
- **时间轴**：slider 回溯历史拓扑状态

---

## 八、核心数据流：告警 → 知识沉淀

```
Phase 1: 告警触发
  Zabbix/SigNoz Webhook → M3 Alert Gateway
    → EventWall 记录 alert.triggered (correlation_id=<new>)

Phase 2: 并行取证（异步）
  ├── M3 证据收集 (C3.8) → 拉取 M5 配置 + M4 日志 + SNMP 状态
  ├── M8 证据编排 (H8.8) → 整理关联 + M7 知识库上下文
  ├── M8 跨层分析 (H8.10) → M6 跨层数据 + 服务拓扑
  └── EventWall 故障评分 → 更新 fault cluster score

Phase 3: AI 根因分析
  M8 Agent: Preflight → Skill: alert_triage → ReAct 循环
    → 调用 query_evidence / query_knowledge / query_cross_layer
    → 发布 analysis.completed（根因 + 置信度 + 证据链）

Phase 4: 人工处置
  前端展示：证据时间线 + 根因卡片 + 知识建议 + 操作按钮
  工程师 → 认领 → 处理 → 解决

Phase 5: 知识归档
  alert.resolved → M7 自动生成案例草稿 → 人工确认 → pgvector 索引入库
  EventWall correlation_id 闭环：所有事件可追溯
```

---

## 九、数据库设计

### 9.1 存储引擎选型

| 数据域 | 存储引擎 | 理由 |
|--------|---------|------|
| 设备资产、IPAM、用户角色、知识库 | PostgreSQL | 关系型、ACID、复杂关联 |
| 性能指标、告警实例、日志、EventWall 事件 | TimescaleDB（PG 扩展） | 时序优化、自动分区、压缩 |
| 会话缓存、实时状态、Celery Broker | Redis | 内存级、TTL、Pub/Sub |
| 配置文件备份、巡检报告 | MinIO（S3 兼容） | 大文件、版本管理、AES-256 |
| 知识库向量嵌入 | pgvector（PG 扩展） | 共存、免独立向量库 |
| 知识图谱 | PostgreSQL 邻接表 | 规模内（≤5000 设备），递归 CTE |

### 9.2 关键新增表

**EventWall 事件表（TimescaleDB hypertable）**：

| 字段分组 | 字段 | 说明 |
|---------|------|------|
| 标识 | id, event_type, event_version | 事件唯一标识 |
| 来源 | source_module, source_component | 哪个模块/组件产生 |
| 时间 | timestamp, received_at | 事件时间 + 接收时间 |
| 生产者 | producer_type, producer_user_id, producer_agent_session_id | system/webhook/user/agent |
| 关联 | correlation_id, parent_event_id, root_event_id, fault_id, incident_id | 业务流 + 故障 + 父事件树 |
| 资源 | resource_type, resource_id, resource_name, resource_module | 事件关联的实体 |
| 分类 | severity, status | info/critical/emergency + new/completed/failed |
| 数据 | payload, tags, metrics | JSONB 自由扩展 |
| 上下文 | context_ip_address, context_request_id | 请求溯源 |
| 保留 | retention_ttl_days | 单事件级 TTL |

**Agent 审计表**：

| 表 | 用途 |
|---|------|
| `agent_sessions` | 会话元数据（模式、Skill、Token 数、费用） |
| `agent_tool_calls` | 每次工具调用记录（名称、参数、延迟、状态） |
| `agent_llm_calls` | 每次 LLM 调用（模型、Token、费用） |
| `agent_preflight_logs` | 安全检查记录（权/险/依/回） |
| `agent_pending_actions` | 待确认动作（含 TTL） |

---

## 十、项目目录结构

```
backend/
├── app/
│   ├── main.py                          # FastAPI 工厂、中间件、路由注册
│   ├── config/settings.py               # Pydantic Settings
│   ├── modules/
│   │   ├── module1_asset/               # M1: 设备资产管理
│   │   ├── module2_ipam/                # M2: IP 地址管理
│   │   ├── module3_monitoring/          # M3: 基础设施监控与告警
│   │   ├── module4_log/                 # M4: 日志分析
│   │   ├── module5_config/              # M5: 配置备份与自动化
│   │   ├── module6_apm/                 # M6: 应用性能监控
│   │   ├── module7_knowledge/           # M7: 知识库
│   │   ├── module8_ai/                  # M8: AI 智能引擎 ★重设计
│   │   │   ├── agent/                   # Action Router + Preflight + Executor
│   │   │   ├── tools/                   # Tool Registry + 内置工具
│   │   │   ├── capabilities/            # 7 个内置 Skill 实现
│   │   │   ├── llm/                     # LLM 客户端封装
│   │   │   └── knowledge_graph/         # 知识图谱引擎
│   │   ├── module9_platform/            # M9: 平台基础 + RBAC
│   │   │   ├── auth/                    # 认证
│   │   │   ├── audit/                   # 审计日志
│   │   │   └── permission_registry.py   # 90 权限码 + 7 内置角色
│   │   ├── module10_eventwall/          # M10: 事件墙 ★新建
│   │   │   ├── models.py               # EventRecord (28 字段) + FaultCluster
│   │   │   ├── service.py              # EventService + FaultAnalysisService
│   │   │   ├── api.py                  # 8 个 API 端点
│   │   │   └── repository.py           # 数据访问层
│   │   └── module11_scheduler/          # M11: 调度与集成网关
│   ├── integrations/                    # 外部系统适配器
│   ├── core/
│   │   ├── database/
│   │   │   ├── session.py              # AsyncSession 工厂
│   │   │   ├── base.py                 # Declarative Base
│   │   │   ├── mixins.py               # Timestamp/UUID/SoftDelete
│   │   │   └── event_mixin.py          # EventRecordingMixin ★
│   │   ├── cache/redis.py
│   │   ├── message_queue/event_bus.py
│   │   ├── storage/object_storage.py
│   │   ├── scheduler/celery_app.py
│   │   └── middleware/
│   │       ├── auth.py                 # JWT 验证
│   │       ├── permissions.py          # require_permission 装饰器 ★
│   │       └── demo_guard.py           # DemoGuardMiddleware ★
│   └── shared/
│
├── frontend/
│   └── src/
│       ├── routes.tsx                   # 26 路由
│       ├── api/                         # 按模块分离的 API 层
│       ├── layouts/MainLayout.tsx       # 动态侧边栏（按权限显示）
│       ├── pages/                       # 17 个功能页面
│       ├── components/
│       │   ├── ai/                      # AI Chat Widget (FAB + 嵌入)
│       │   ├── charts/                  # ECharts 封装
│       │   ├── topology/                # ReactFlow 拓扑图
│       │   └── diff/                    # Monaco 配置 Diff
│       ├── stores/                      # Zustand + TanStack Query
│       └── types/                       # TypeScript 类型
│
├── shared/                              # 跨端契约
├── deploy/                              # Docker Compose
└── docs/                                # 文档
```

---

## 十一、实施路线图

| 阶段 | 内容 | 关键交付 | 状态 |
|------|------|---------|------|
| **Phase 1** | 脚手架搭建 | FastAPI 工厂、JWT、DB Session、前端框架、Docker | ✅ |
| **Phase 2** | EventWall + RBAC | M10 事件墙、90 权限码、`require_permission`、7 角色、Demo 守卫、ORM Mixin | ✅ |
| **Phase 3** | Agent 引擎重设计 | Action Router、Preflight、Skill 系统、Tool Registry、5 审计表、SSE 端点、3 个内置 Skill | 待实施 |
| **Phase 4** | 数据底座（M1/M2/M5） | 设备 CRUD + 校准、IPAM、配置备份 + Diff、EventRecordingMixin 全应用、22 个 API 端点 | ✅ |
| **Phase 5** | 监控闭环（M3） | 告警状态机、Webhook 接入、规则引擎、降噪去重、证据收集、通知策略、14 个 API 端点 | ✅ |
| **Phase 6** | APM 集成（M6） | SigNoz 适配器、跨层映射、跨层定界 Skill、3 表 7 端点 | ✅ |
| **Phase 7** | 知识库 + 图谱（M7 + M8 Graph） | pgvector、全文搜索、自动归档、知识图谱邻接表 | ✅ |
| **Phase 8** | AI 对话前端 | SSE 流式端点、FAB 浮窗框架、富卡片、待确认动作 UI | ✅ |
| **Phase 9** | 日志 + 完善（M4） | Syslog/API 日志汇聚、TimescaleDB、关键字检索 | ✅ |

---

## 十二、架构决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| **Agent 编排** | 自定义 Preflight + LangChain Executor | LangChain 处理 LLM 循环，自定义代码处理安全关卡 |
| **EventWall 存储** | TimescaleDB | 统一引擎、自动压缩、连续聚合、与指标/告警共存 |
| **事件采集** | SQLAlchemy 事件监听器 | 零侵入，模块开发者无需手动埋点 |
| **权限强制执行** | 装饰器 `@require_permission` | 精细到 API 端点级别，FastAPI Depends 原生支持 |
| **知识图谱** | PG 邻接表 + ReactFlow | 规模内（≤5000 设备），免图数据库运维 |
| **聊天流式** | SSE + polling 回退 | 比 WebSocket 更简单，代理兼容性好 |
| **演示保护** | 权限码 + 中间件双重 | 纵深防御：权限层阻止 + HTTP 层拦截 |
| **模块通信** | Interface 注入 + EventWall 事件总线 | 同步用接口，异步用事件，编译时解耦 + 运行时解耦 |
| **LangChain 范围** | 限 Executor 层 | 编排和安全逻辑必须自定义控制 |
| **前端状态** | Zustand + TanStack Query | UI 状态与服务端状态职责分离 |

---

## 十三、Phase 4 数据底座 API 参考

### M1 设备资产管理（10 端点）

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/v1/devices` | GET | 设备列表（支持 device_type/vendor/status/keyword 筛选） | `asset:device:list` |
| `/api/v1/devices` | POST | 创建设备 | `asset:device:create` |
| `/api/v1/devices/{id}` | GET | 设备详情 | `asset:device:retrieve` |
| `/api/v1/devices/{id}/update` | POST | 更新设备 | `asset:device:update` |
| `/api/v1/devices/{id}/delete` | POST | 软删除设备 | `asset:device:delete` |
| `/api/v1/devices/{id}/ips` | GET | 设备关联 IP | `asset:device:retrieve` |
| `/api/v1/devices/{id}/alerts` | GET | 设备关联告警 | `asset:device:retrieve` |
| `/api/v1/calibrations` | GET | 校准报告列表 | `asset:calibration:list` |
| `/api/v1/calibrations/run` | POST | 触发 SNMP/SSH 校准 | `asset:calibration:execute` |
| `/api/v1/calibrations/{id}/approve` | POST | 确认/拒绝校准差异 | `asset:calibration:approve` |

### M2 IP 地址管理（7 端点）

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/v1/ipam/subnets` | GET | 子网列表 | `ipam:subnet:list` |
| `/api/v1/ipam/subnets` | POST | 创建子网（自动计算 total_ips） | `ipam:subnet:create` |
| `/api/v1/ipam/subnets/{id}/update` | POST | 更新子网 | `ipam:subnet:update` |
| `/api/v1/ipam/subnets/{id}/delete` | POST | 删除子网 | `ipam:subnet:delete` |
| `/api/v1/ipam/allocations` | GET | IP 分配列表 | `ipam:ip:list` |
| `/api/v1/ipam/allocations/allocate` | POST | 分配 IP（自动更新 used_ips） | `ipam:ip:allocate` |
| `/api/v1/ipam/allocations/{id}/release` | POST | 释放 IP | `ipam:ip:release` |

### M5 配置备份与自动化（5 端点）

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/v1/configs/backups` | GET | 备份列表 | `config:backup:list` |
| `/api/v1/configs/backups/trigger` | POST | 触发配置备份（生成 SHA256 + diff） | `config:backup:trigger` |
| `/api/v1/configs/diffs` | GET | Diff 列表 | `config:diff:view` |
| `/api/v1/configs/diff/{device_id}` | GET | 设备最新配置 Diff（含风险评级） | `config:diff:view` |

### 模块数据库表（6 张新表）

| 表 | 所属模块 | 关键字段 |
|----|---------|---------|
| `devices` | M1 | device_name, device_type, vendor, model, extra_attrs(JSONB), deleted_at(软删除) |
| `calibration_reports` | M1 | device_id(FK), source, field_name, status(pending/confirmed/rejected) |
| `subnets` | M2 | cidr(UNIQUE), vlan_id, gateway, total_ips, used_ips |
| `ip_allocations` | M2 | subnet_id(FK), ip_address, status(free/allocated/reserved), device_id(FK) |
| `config_backups` | M5 | device_id(FK), backup_type, status, config_hash(SHA256), file_size |
| `config_diffs` | M5 | device_id(FK), old/new_backup_id(FK), diff_content, risk_level(normal/suspicious/high) |

> 所有表均使用 `EventRecordingMixin`，CRUD 操作自动发布 EventWall 事件。所有写操作遵循 POST 约定，无 PUT/DELETE 方法。


## 附录 A：事件 Schema 标准

所有领域事件通过 EventWall 发布，使用统一的 28 字段 Schema（见 3.2 节）。

## 附录 B：API 响应格式标准

**成功响应**：
```json
{ "id": "uuid", "field": "value" }
```

**列表响应**：
```json
{ "total": 100, "items": [] }
```

**错误响应**：
```json
{ "code": "FORBIDDEN", "message": "Permission denied: requires 'asset:device:update'" }
```

**202 Accepted（异步事件）**：
```json
{ "event_id": "uuid", "status": "accepted" }
```

## 附录 C：告警状态机

```
TRIGGERED → ACKNOWLEDGED → IN_PROGRESS → RESOLVED → CLOSED
    │            │               │
    └─(降噪)     └─(超时升级)     └─(自动归档→M7)
```

## 附录 D：权限码通配符继承

```
*:*:*           superadmin 全部权限
asset:*:*       asset 模块全部操作
asset:device:*  device 资源全部 CRUD
asset:device:list  特定权限码
```
