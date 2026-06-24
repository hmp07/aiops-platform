# AIOps Platform

AI 增强型智能运维管理平台 — 以受控编排、事件驱动、精细权限、人机协作为核心理念，打通设备资产、IP 管理、基础设施监控、日志分析、配置管理、应用性能监控、知识库、AI 智能运维和事件墙的完整链条。

## 架构概览

```
11 模块  |  FastAPI + React + TimescaleDB + Redis + MinIO + LangChain
```

| 模块 | 名称 | 状态 |
|------|------|------|
| M1 | 设备资产管理 | 待实施 |
| M2 | IP 地址管理 | 待实施 |
| M3 | 基础设施监控与告警 | 待实施 |
| M4 | 日志分析 | 待实施 |
| M5 | 配置备份与自动化 | 待实施 |
| M6 | 应用性能监控 | 待实施 |
| M7 | 知识库 | 待实施 |
| M8 | AI 智能引擎 | ✅ Phase 3 |
| M9 | 平台基础 + RBAC | ✅ Phase 2 |
| M10 | EventWall 事件墙 | ✅ Phase 2 |
| M11 | 调度与集成网关 | 待实施 |

## 快速开始

### Docker 部署

```bash
# 1. 拉取镜像
docker pull timescale/timescaledb:latest-pg16
docker pull redis:7-alpine
docker pull minio/minio
docker pull python:3.12-slim
docker pull node:22-alpine
docker pull nginx:alpine

# 2. 构建并启动
docker compose -f deploy/docker-compose.yml up -d --build

# 3. 访问
# 前端: http://localhost
# API 文档: http://localhost:8000/api/docs
```

### 本地开发

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # 编辑数据库连接
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Demo（独立演示项目）

```bash
cd demo
docker compose up -d --build
# 访问 http://localhost
# 账号: admin / admin123
```

## 项目结构

```
├── backend/                    # Python FastAPI 后端
│   └── app/
│       ├── main.py             # 应用入口
│       ├── modules/            # 11 个业务模块
│       │   ├── module1_asset/  # M1-M7, M11
│       │   ├── module8_ai/     # AI 引擎 (Action Router + Preflight + Skills + Tools)
│       │   ├── module9_platform/  # 平台 + RBAC (90 权限码 + 7 角色)
│       │   └── module10_eventwall/ # 事件墙 (28 字段 Schema + 故障分析)
│       ├── integrations/       # 外部系统适配器
│       ├── core/               # 基础设施 (DB/Redis/EventBus/Celery/MinIO)
│       └── shared/             # 共享工具
├── frontend/                   # React + TypeScript 前端
├── demo/                       # 独立演示项目（模拟数据，开箱即用）
├── deploy/                     # Docker Compose 部署
└── docs/                       # 架构文档
```

## 核心特性

### AI Agent 引擎 (M8)

- **Action Router**: 三模式分类（Direct / ReAct / Plan+ReAct）
- **Preflight 安全关卡**: 权限 → 风险 → 依赖 → 回滚 四步检查
- **Skill 系统**: 可插拔领域能力包（告警分诊、配置风险分析、巡检报告）
- **Tool Registry**: 动态工具发现 + RBAC 过滤 + 风险等级过滤
- **两阶段安全**: 只读直达 / 写入待确认
- **SSE 流式响应**: 9 种事件类型的实时流

### EventWall 事件墙 (M10)

- 28 字段通用事件 Schema
- ORM 事件监听器自动采集 CRUD
- 外部 Webhook 接入 + Token 认证
- 故障分析引擎（滑动窗口 + 加权评分聚类）

### RBAC 权限系统 (M9)

- 90 权限码（`module:resource:action`）
- 7 内置角色（superadmin / admin / operator / engineer / viewer / auditor / demo）
- 端点级 `@require_permission` 装饰器
- Demo 账号写操作拦截

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python FastAPI (async) |
| 前端框架 | React 19 + TypeScript + Ant Design 5 |
| 数据库 | PostgreSQL + TimescaleDB |
| 缓存/消息 | Redis |
| 对象存储 | MinIO (S3) |
| AI Agent | LangChain Executor + 自定义编排 |
| 任务调度 | Celery |
| 向量搜索 | pgvector |
| 网络自动化 | Netmiko + PySNMP |
| 部署 | Docker Compose |

## 架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Agent 编排 | 自定义 Preflight + LangChain Executor | 安全关卡自定义，LLM 循环复用 |
| EventWall 存储 | TimescaleDB | 统一引擎，自动压缩 |
| 事件采集 | SQLAlchemy 事件监听器 | 零侵入 |
| 权限执行 | `@require_permission` 装饰器 | 端点级精细控制 |
| 聊天流式 | SSE + polling 回退 | 比 WebSocket 更简单 |
| API 方法 | 仅 GET + POST | 统一简洁 |

## 许可证

MIT
