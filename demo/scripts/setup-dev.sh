#!/bin/bash
# ============================================================
# AIOps Platform Demo — 开发模式一键部署脚本
# 适用系统: Rocky Linux 9.x
# 用法: bash setup-dev.sh [--frontend-only] [--backend-only]
# ============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[ OK ]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

DEPLOY_MODE="all"
for arg in "$@"; do
    case $arg in --frontend-only) DEPLOY_MODE="frontend" ;; --backend-only) DEPLOY_MODE="backend" ;; esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEMO_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$DEMO_DIR/backend"
FRONTEND_DIR="$DEMO_DIR/frontend"
VENV_DIR="$DEMO_DIR/.venv"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  AIOps Platform Demo — 开发模式部署${NC}"
echo -e "${BLUE}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# ============================================
# 1. 系统依赖检查与安装
# ============================================
log_info "Step 1/6: 检测系统依赖..."

install_sys_deps() {
    local missing=""
    for pkg in python3.12 python3.12-pip python3.12-devel nodejs git curl; do
        if ! command -v ${pkg%%-*} &>/dev/null && ! rpm -q $pkg &>/dev/null 2>&1; then
            missing="$missing $pkg"
        fi
    done
    # 特殊处理: python3.12 的检测
    if ! command -v python3.12 &>/dev/null; then
        missing="$missing python3.12"
    fi
    if ! command -v node &>/dev/null; then
        missing="$missing nodejs"
    fi

    if [ -n "$missing" ]; then
        log_warn "缺少以下系统包:$missing"
        read -p "  是否自动安装? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "安装 EPEL 和 NodeSource 仓库..."
            dnf install -y epel-release 2>/dev/null || true
            if ! command -v node &>/dev/null; then
                curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
            fi
            log_info "安装系统依赖..."
            dnf install -y python3.12 python3.12-pip python3.12-devel nodejs git curl
            log_ok "系统依赖安装完成"
        else
            log_error "请手动安装依赖后重试"
            exit 1
        fi
    else
        log_ok "系统依赖已就绪"
    fi
}

if [ "$DEPLOY_MODE" != "frontend" ]; then
    install_sys_deps
else
    if ! command -v node &>/dev/null; then
        log_warn "缺少 Node.js"
        read -p "  是否自动安装? [y/N] " -n 1 -r; echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
            dnf install -y nodejs
        fi
    fi
fi

# ============================================
# 2. 后端部署
# ============================================
if [ "$DEPLOY_MODE" != "frontend" ]; then
    echo ""
    log_info "Step 2/6: 配置 Python 虚拟环境..."

    if [ ! -d "$VENV_DIR" ]; then
        python3.12 -m venv "$VENV_DIR"
        log_ok "虚拟环境已创建: $VENV_DIR"
    else
        log_ok "虚拟环境已存在"
    fi

    source "$VENV_DIR/bin/activate"

    echo ""
    log_info "Step 3/6: 安装 Python 依赖..."
    pip install --upgrade pip -q
    pip install -r "$BACKEND_DIR/requirements.txt" -q
    log_ok "Python 依赖安装完成"

    echo ""
    log_info "Step 4/6: 启动后端服务..."
    cd "$BACKEND_DIR"

    # 创建 systemd 服务文件提示
    log_info "启动命令: uvicorn main:app --host $BACKEND_HOST --port $BACKEND_PORT --reload"
    echo ""
    log_info "后端服务将在以下地址运行:"
    echo "       API 文档: http://<server-ip>:$BACKEND_PORT/api/docs"
    echo "      健康检查: http://<server-ip>:$BACKEND_PORT/api/health"
fi

# ============================================
# 3. 前端部署
# ============================================
if [ "$DEPLOY_MODE" != "backend" ]; then
    echo ""
    log_info "Step 5/6: 安装前端依赖..."

    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        npm install
        log_ok "前端依赖安装完成"
    else
        log_ok "前端依赖已存在"
    fi

    echo ""
    log_info "Step 6/6: 启动前端开发服务器..."
    log_info "启动命令: npm run dev"
    echo ""
    log_info "前端开发服务器将在以下地址运行:"
    echo "       前端页面: http://<server-ip>:$FRONTEND_PORT"
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}  开发环境部署准备完成！${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# ============================================
# 输出启动说明
# ============================================
cat << 'STARTUP'
  启动服务 (在两个终端中分别执行):

  终端 1 — 后端:
    cd AIOps-Platform/demo/backend
    source ../.venv/bin/activate
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  终端 2 — 前端:
    cd AIOps-Platform/demo/frontend
    npm run dev

  访问:
    前端主页: http://<server-ip>:3000
    API 文档: http://<server-ip>:8000/api/docs
    健康检查: http://<server-ip>:8000/api/health

  演示账号:
    admin    / admin123      (管理员)
    engineer / engineer123   (运维工程师)
    viewer   / viewer123     (只读观察员)

  停止服务:
    两个终端分别按 Ctrl+C

STARTUP

# ============================================
# 询问是否立即启动
# ============================================
read -p "是否立即启动服务? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    log_info "启动后端服务 (后台运行)..."
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    nohup uvicorn main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload > "$DEMO_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "  后端 PID: $BACKEND_PID (日志: $DEMO_DIR/backend.log)"

    sleep 2
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_ok "后端已启动 (PID: $BACKEND_PID)"
    else
        log_error "后端启动失败，请查看日志: $DEMO_DIR/backend.log"
    fi

    echo ""
    log_info "启动前端开发服务器..."
    cd "$FRONTEND_DIR"
    nohup npm run dev -- --host 0.0.0.0 > "$DEMO_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "  前端 PID: $FRONTEND_PID (日志: $DEMO_DIR/frontend.log)"

    sleep 3
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_ok "前端已启动 (PID: $FRONTEND_PID)"
    else
        log_error "前端启动失败，请查看日志: $DEMO_DIR/frontend.log"
    fi

    echo ""
    echo -e "${GREEN}服务已启动！${NC}"
    echo "  后端: http://localhost:$BACKEND_PORT"
    echo "  前端: http://localhost:$FRONTEND_PORT"
    echo "  停止服务: kill $BACKEND_PID $FRONTEND_PID"
fi
