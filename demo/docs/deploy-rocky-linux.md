# AIOps Platform Demo — Rocky Linux 9.7 部署手册

---

**适用系统**: Rocky Linux 9.x / RHEL 9.x / CentOS Stream 9
**部署模式**: 开发模式（直接运行）→ Docker 模式（生产演示）
**最后更新**: 2026-05-28

---

## 目录

1. [环境要求](#一环境要求)
2. [环境检测](#二环境检测)
3. [开发模式部署](#三开发模式部署)
4. [服务管理](#四服务管理)
5. [Docker 模式部署](#五docker-模式部署)
6. [验证测试](#六验证测试)
7. [故障排查](#七故障排查)
8. [安全加固（可选）](#八安全加固可选)

---

## 一、环境要求

### 1.1 硬件最低要求

| 资源 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 2 GB | 4 GB |
| 磁盘 | 5 GB 可用 | 10 GB 可用 |
| 网络 | 可访问外网（安装依赖） | — |

### 1.2 软件要求

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Rocky Linux | 9.x | 操作系统 |
| Python | 3.10 ~ 3.12 | 后端运行环境 |
| Node.js | 20 LTS ~ 22 LTS | 前端构建/运行 |
| npm | 9.x ~ 10.x | 前端包管理 |
| Git | 任意 | 项目拉取 |

### 1.3 端口要求

| 端口 | 用途 | 模式 |
|------|------|------|
| 8000 | 后端 API (FastAPI) | 全部 |
| 3000 | 前端 Vite Dev Server | 仅开发模式 |
| 80 | 前端 Nginx | 仅 Docker 模式 |

---

## 二、环境检测

### 2.1 运行检测脚本

将项目上传到服务器后，先运行环境检测：

```bash
cd AIOps-Platform/demo
bash scripts/check-env.sh
```

检测脚本会检查 9 大类共 30+ 项：
1. 操作系统版本与架构
2. Python 版本与 venv 模块
3. Node.js 与 npm 版本
4. 基础工具（curl, wget, git, gcc, make）
5. 外网连通性（PyPI, npm Registry）
6. 端口占用情况（8000, 3000）
7. 系统资源（内存、磁盘、CPU）
8. Python 关键包预检
9. 防火墙状态

### 2.2 检测结果解读

```
通过: N   — 正常，无需处理
警告: N   — 建议修复，但不会阻塞部署
失败: N   — 必须修复，否则部署会出错
```

### 2.3 安装缺失的依赖

```bash
# 安装 EPEL 仓库
dnf install -y epel-release

# 安装 Python 3.12
dnf install -y python3.12 python3.12-pip python3.12-devel python3.12-venv

# 安装 Node.js 22 LTS
curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
dnf install -y nodejs

# 验证安装
python3.12 --version   # 应输出 Python 3.12.x
node --version          # 应输出 v22.x.x
npm --version           # 应输出 10.x.x

# 安装基础工具
dnf install -y curl wget git gcc make
```

---

## 三、开发模式部署

开发模式适用于快速验证和调试，服务直接运行在宿主机上，支持热重载。

### 3.1 项目准备

```bash
# 方式一: Git 克隆（如果有 Git 仓库）
git clone <repository-url>
cd AIOps-Platform/demo

# 方式二: 上传压缩包
# 在本地执行:
#   tar -czf demo.tar.gz demo/
#   scp demo.tar.gz root@<server-ip>:/opt/
# 在服务器执行:
#   cd /opt && tar -xzf demo.tar.gz
#   cd demo
```

### 3.2 一键自动部署

```bash
# 完整部署（后端 + 前端）
bash scripts/setup-dev.sh

# 仅部署后端
bash scripts/setup-dev.sh --backend-only

# 仅部署前端
bash scripts/setup-dev.sh --frontend-only
```

脚本会自动完成：
1. 检测并安装系统依赖（需确认）
2. 创建 Python 虚拟环境
3. 安装 Python 依赖
4. 安装前端 npm 依赖
5. 询问是否立即启动服务

### 3.3 手动分步部署

如果自动脚本不可用，按以下步骤手动部署：

#### Step 1: 创建 Python 虚拟环境

```bash
cd demo
python3.12 -m venv .venv
source .venv/bin/activate
```

#### Step 2: 安装后端依赖

```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# 验证安装
python -c "from main import app; print('Backend OK, routes:', len(app.routes))"
# 应输出: Backend OK, routes: 43
```

#### Step 3: 启动后端服务

```bash
# 前台启动（开发调试，Ctrl+C 停止）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 后台启动
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
echo $! > ../backend.pid
```

#### Step 4: 安装前端依赖

```bash
cd ../frontend
npm install
```

#### Step 5: 启动前端服务

```bash
# 开发模式（支持热重载，默认端口 3000）
npm run dev -- --host 0.0.0.0

# 后台启动
nohup npm run dev -- --host 0.0.0.0 > ../frontend.log 2>&1 &
echo $! > ../frontend.pid
```

### 3.4 配置防火墙

```bash
# 方式一: 开放端口（推荐）
firewall-cmd --add-port=8000/tcp --permanent
firewall-cmd --add-port=3000/tcp --permanent
firewall-cmd --reload

# 方式二: 临时关闭防火墙（仅开发环境）
systemctl stop firewalld

# 验证端口开放
firewall-cmd --list-ports
```

### 3.5 访问验证

```bash
# 本地验证
curl http://localhost:8000/api/health
# 应输出: {"status":"ok","version":"1.0.0","mode":"demo"}

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# 应返回 JWT token 和用户信息

# 远程访问
# 浏览器打开: http://<server-ip>:3000
```

---

## 四、服务管理

### 4.1 进程管理

```bash
# 查看服务状态
ps aux | grep -E "(uvicorn|vite)" | grep -v grep

# 查看日志
tail -f backend.log
tail -f frontend.log

# 停止服务
kill $(cat backend.pid)
kill $(cat frontend.pid)
# 或
pkill -f "uvicorn main:app"
pkill -f "vite"
```

### 4.2 配置 systemd 服务（可选）

创建后端服务：

```bash
cat > /etc/systemd/system/aiops-demo-backend.service << 'EOF'
[Unit]
Description=AIOps Demo Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/demo/backend
Environment="PATH=/opt/demo/.venv/bin"
ExecStart=/opt/demo/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

创建前端服务（开发模式）：

```bash
cat > /etc/systemd/system/aiops-demo-frontend.service << 'EOF'
[Unit]
Description=AIOps Demo Frontend (Vite Dev)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/demo/frontend
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 3000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

启用服务：

```bash
systemctl daemon-reload
systemctl enable --now aiops-demo-backend
systemctl enable --now aiops-demo-frontend

# 管理命令
systemctl status aiops-demo-backend
systemctl restart aiops-demo-backend
systemctl stop aiops-demo-backend
journalctl -u aiops-demo-backend -f
```

### 4.3 快速操作命令速查

```bash
# ---- 开发模式 ----
# 启动
bash scripts/setup-dev.sh                    # 一键部署+启动
source .venv/bin/activate && cd backend && \
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload &  # 后端
cd frontend && npm run dev -- --host 0.0.0.0 &             # 前端

# 停止
pkill -f "uvicorn main:app"
pkill -f "vite"

# 重启
pkill -f "uvicorn main:app" && sleep 1 && \
  cd backend && source ../.venv/bin/activate && \
  nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &

# 查看日志
tail -100 backend.log
tail -100 frontend.log

# ---- systemd 模式 ----
systemctl start/stop/restart aiops-demo-backend
systemctl start/stop/restart aiops-demo-frontend
journalctl -u aiops-demo-backend -f
```

---

## 五、Docker 模式部署

开发模式验证无误后，可切换为 Docker 模式获得更稳定的演示环境。

### 5.1 安装 Docker

```bash
# 安装 Docker
dnf config-manager --add-repo https://download.docker.com/linux/rocky/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
systemctl enable --now docker

# 验证
docker --version
docker compose version
```

### 5.2 构建并启动

```bash
cd demo

# 构建镜像并启动（后台运行）
docker compose up -d --build

# 查看运行状态
docker compose ps
docker compose logs -f

# 停止
docker compose down
```

### 5.3 Docker 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | Nginx 静态资源 + API 代理 |
| api | 8000 | FastAPI 后端 |

### 5.4 防火墙配置

```bash
# Docker 模式只需要开放 80 端口
firewall-cmd --add-port=80/tcp --permanent
firewall-cmd --reload
```

### 5.5 访问

```
http://<server-ip>
```

---

## 六、验证测试

### 6.1 API 端点测试

```bash
SERVER_IP="localhost"  # 或实际服务器 IP

# 1. 健康检查
curl -s http://$SERVER_IP:8000/api/health | python3 -m json.tool

# 2. 登录测试
curl -s -X POST http://$SERVER_IP:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -m json.tool

# 3. 仪表盘数据
curl -s http://$SERVER_IP:8000/api/v1/dashboard/stats | python3 -m json.tool

# 4. 设备列表
curl -s http://$SERVER_IP:8000/api/v1/devices?page_size=5 | python3 -m json.tool

# 5. 告警详情（含 AI 分析）
curl -s http://$SERVER_IP:8000/api/v1/alerts/a1 | python3 -m json.tool

# 6. 服务拓扑
curl -s http://$SERVER_IP:8000/api/v1/apm/topology | python3 -m json.tool

# 7. AI 巡检报告
curl -s http://$SERVER_IP:8000/api/v1/ai/inspection-reports | python3 -m json.tool

# 8. 知识库
curl -s http://$SERVER_IP:8000/api/v1/knowledge/articles | python3 -m json.tool
```

### 6.2 前端页面测试

在浏览器中依次验证：

| # | 页面 | URL | 验证要点 |
|---|------|-----|---------|
| 1 | 登录 | /login | 三个演示账号均可登录 |
| 2 | 仪表盘 | /dashboard | 统计卡片、告警趋势图、最近告警 |
| 3 | 设备列表 | /asset | 20 台设备展示、过滤功能 |
| 4 | 设备详情 | /asset/d1 | 设备信息、关联 IP、关联告警 |
| 5 | IP 管理 | /ipam | 子网使用率、IP 分布饼图 |
| 6 | 告警列表 | /monitoring/alerts | 15 条告警、严重级别彩色标签 |
| 7 | 告警详情 a1 | /monitoring/alerts/a1 | **核心**: AI 根因分析、证据时间线、配置变更 |
| 8 | 告警详情 a2 | /monitoring/alerts/a2 | **核心**: 跨层故障定界、进度环 |
| 9 | 配置管理 | /config/backups | 备份列表、配置 Diff Modal (Monaco Editor) |
| 10 | 服务列表 | /apm/services | 8 个服务状态 |
| 11 | 服务拓扑 | /apm/topology | **核心**: ReactFlow 三层拓扑图 |
| 12 | AI 问答 | /ai/chat | **核心**: 5 个预置问题、流式响应 |
| 13 | 巡检报告 | /ai/inspection | Markdown 渲染的周报 |
| 14 | 知识库 | /knowledge | 搜索、文章详情 |
| 15 | 用户管理 | /admin/users | 3 个演示用户 |
| 16 | 审计日志 | /admin/audit | 5 条操作记录 |
| 17 | 日志检索 | /log/explorer | 模拟日志数据 |

---

## 七、故障排查

### 7.1 后端无法启动

```bash
# 检查端口占用
ss -tlnp | grep 8000

# 检查 Python 版本
python3.12 --version

# 检查虚拟环境
source .venv/bin/activate
pip list | grep -E "fastapi|uvicorn"

# 手动测试导入
python -c "from main import app"
```

### 7.2 前端无法启动

```bash
# 检查 Node.js 版本
node --version  # 需要 >= 20

# 清除缓存重装
cd frontend
rm -rf node_modules package-lock.json
npm install

# 检查端口
ss -tlnp | grep 3000

# 手动启动查看错误
npm run dev -- --host 0.0.0.0
```

### 7.3 前端访问后端 404/500

开发模式下，前端 Vite Dev Server 会自动将 `/api` 请求代理到 `localhost:8000`。确认：

```bash
# 后端是否在运行
curl http://localhost:8000/api/health

# Vite 代理配置 (vite.config.ts)
# proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true } }
```

### 7.4 远程无法访问

```bash
# 1. 确认服务监听地址
ss -tlnp | grep -E "8000|3000"
# 应显示 0.0.0.0:8000 而非 127.0.0.1:8000

# 2. 检查防火墙
firewall-cmd --list-ports

# 3. 检查 SELinux（临时关闭测试）
getenforce
setenforce 0  # 临时关闭测试

# 4. 测试端口连通性（从客户端）
telnet <server-ip> 8000
curl http://<server-ip>:8000/api/health
```

### 7.5 常见错误速查

| 错误 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: No module named 'fastapi'` | 未安装依赖 | `pip install -r requirements.txt` |
| `npm: command not found` | 未安装 Node.js | 参见 2.3 节安装 Node.js |
| `Error: Cannot find module 'antd'` | npm 依赖未安装 | `cd frontend && npm install` |
| `Address already in use` | 端口被占用 | `ss -tlnp \| grep 端口号`，kill 占用进程 |
| `Connection refused` | 服务未启动或监听 127.0.0.1 | 确认 --host 0.0.0.0 |
| `/api/v1/... 404` | 前端代理未配置 | 检查 vite.config.ts proxy |
| `SELinux is preventing...` | SELinux 拦截 | `setenforce 0`（临时）或配置策略 |

---

## 八、安全加固（可选）

以下措施仅用于对外演示时增强安全性：

```bash
# 1. 限制监听地址（仅内网访问）
# 修改启动命令: --host 192.168.x.x 替代 --host 0.0.0.0

# 2. 配置防火墙白名单
firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.0.0/16" port port="8000" protocol="tcp" accept' --permanent
firewall-cmd --reload

# 3. 恢复 SELinux
setenforce 1

# 4. 使用非 root 用户运行
useradd -r -s /bin/false aiops
chown -R aiops:aiops /opt/demo
# 修改 systemd 服务中的 User=aiops

# 5. 定期清理日志
# 添加 crontab: 0 3 * * * find /opt/demo -name "*.log" -mtime +7 -delete
```

---

## 附录 A：文件清单

```
demo/
├── scripts/
│   ├── check-env.sh          # 环境检测脚本
│   └── setup-dev.sh          # 一键部署脚本
├── docs/
│   └── deploy-rocky-linux.md # 本部署文档
├── backend/
│   ├── main.py               # FastAPI 入口
│   ├── mock_data.py          # 模拟数据
│   ├── requirements.txt      # Python 依赖
│   └── routes/               # 10 个路由模块
├── frontend/
│   ├── package.json          # Node 依赖
│   ├── vite.config.ts        # Vite 配置
│   └── src/pages/            # 17 个功能页面
├── docker-compose.yml        # Docker 部署
└── README.md                 # 项目说明
```

## 附录 B：依赖清单

### Python (requirements.txt)

```
fastapi>=0.115
uvicorn[standard]>=0.34
```

### Node.js (package.json dependencies)

```
react 19, antd 5, @ant-design/pro-table, @ant-design/pro-layout,
echarts-for-react, reactflow, @monaco-editor/react,
zustand, @tanstack/react-query, axios, dayjs, react-markdown,
react-router-dom, @ant-design/icons
```
