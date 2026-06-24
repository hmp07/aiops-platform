# AIOps Platform Demo

AIOps 智能运维管理平台演示项目，用于项目立项和审批演示。

## 快速启动

```bash
cd demo
docker-compose up -d
```

访问 http://localhost

## 演示账号

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | 管理员 | 拥有所有权限 |
| engineer | engineer123 | 运维工程师 | 可处理告警、查看设备 |
| viewer | viewer123 | 只读观察员 | 仅查看 |

## 演示路径

按以下顺序演示可获得最佳效果：

1. **登录** → admin/admin123
2. **仪表盘** → 全局运维态势一览
3. **设备资产** → 20 台模拟设备的全量管理
4. **告警列表** → 15 条不同状态的告警
5. **告警详情 (a1)** → **核心亮点**：AI 根因分析 (C3.9) + 证据时间线 + 配置变更追踪
6. **告警详情 (a2)** → **核心亮点**：AI 跨层故障定界 (H8.10) + APM Trace 分析
7. **配置管理** → CORE-SW-01 配置 Diff + AI 风险评级
8. **服务拓扑** → ReactFlow 三层拓扑图 (服务→主机→交换机)
9. **AI 问答** → 5 个预置问题的智能回答
10. **巡检报告** → AI 自动生成的本周巡检报告
11. **知识库** → 故障案例、应急预案、命令模板

## 技术栈

- **后端**: Python FastAPI + 模拟数据（无需数据库）
- **前端**: React 19 + TypeScript + Ant Design 5 + ECharts + ReactFlow + Monaco Editor
- **部署**: Docker Compose (api + frontend)

## 项目结构

```
demo/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── mock_data.py         # 全部模拟数据
│   └── routes/              # API 路由 (10 个模块)
├── frontend/
│   └── src/pages/           # 17 个功能页面
├── docker-compose.yml       # 一键部署
└── README.md
```

## 与正式项目的区别

| 维度 | Demo | 正式项目 |
|------|------|---------|
| 数据 | 内存模拟数据 | PostgreSQL + TimescaleDB + Redis + MinIO |
| AI | 预设响应 + 模拟延迟 | 真实 LLM (Claude/GPT) + ReAct Agent |
| 外部集成 | 无 | iTop / Zabbix / SigNoz / SSH / SNMP |
| 部署 | 2 容器 (api + nginx) | 7 容器 (含 DB/Cache/Queue/Worker) |
| 前端 | 完全相同 | 完全相同 |
