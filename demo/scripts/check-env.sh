#!/bin/bash
# ============================================================
# AIOps Platform Demo — 环境检测脚本
# 适用系统: Rocky Linux 9.x / RHEL 9.x / CentOS Stream 9
# 用法: bash check-env.sh
# ============================================================

set -e

# ---- 颜色定义 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
WARN=0
FAIL=0

log_pass()  { echo -e "  ${GREEN}[✓]${NC} $1"; PASS=$((PASS + 1)); }
log_warn()  { echo -e "  ${YELLOW}[!]${NC} $1"; WARN=$((WARN + 1)); }
log_fail()  { echo -e "  ${RED}[✗]${NC} $1"; FAIL=$((FAIL + 1)); }

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  AIOps Platform Demo — 环境检测${NC}"
echo -e "${BLUE}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# ---- 1. 操作系统检测 ----
echo -e "${BLUE}[1/9] 操作系统检测${NC}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "  操作系统: $NAME $VERSION"
    if [[ "$ID" =~ ^(rocky|rhel|centos|almalinux)$ ]]; then
        if [[ "$VERSION_ID" =~ ^9 ]]; then
            log_pass "操作系统 $NAME $VERSION_ID 符合要求 (RHEL 9 系列)"
        else
            log_warn "操作系统版本 $VERSION_ID，推荐 9.x 系列"
        fi
    else
        log_warn "非 RHEL 9 系列系统 ($ID)，可能存在兼容性问题"
    fi
else
    log_fail "无法检测操作系统版本"
fi

ARCH=$(uname -m)
echo "  架构: $ARCH"
if [ "$ARCH" == "x86_64" ]; then
    log_pass "CPU 架构 x86_64"
else
    log_warn "CPU 架构 $ARCH (推荐 x86_64)"
fi

echo ""

# ---- 2. Python 环境 ----
echo -e "${BLUE}[2/9] Python 环境检测${NC}"

PYTHON_BIN=""
for py in python3.12 python3.11 python3.10 python3; do
    if command -v $py &>/dev/null; then
        PYTHON_BIN=$py
        break
    fi
done

if [ -n "$PYTHON_BIN" ]; then
    PY_VER=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo $PY_VER | cut -d. -f1)
    PY_MINOR=$(echo $PY_VER | cut -d. -f2)
    echo "  Python 路径: $(command -v $PYTHON_BIN)"
    echo "  Python 版本: $PY_VER"

    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        log_pass "Python 版本 >= 3.10 ($PY_VER)"
    elif [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 9 ]; then
        log_warn "Python 3.9 可用，但推荐 >= 3.10 ($PY_VER)"
    else
        log_fail "Python 版本过低 ($PY_VER)，需要 >= 3.10"
    fi
else
    log_fail "未找到 Python 3，请安装: dnf install -y python3.12"
    PYTHON_BIN="python3"
fi

# 检测 pip
if command -v pip3.12 &>/dev/null; then
    PIP_BIN="pip3.12"
elif command -v pip3 &>/dev/null; then
    PIP_BIN="pip3"
else
    PIP_BIN="pip3"
    log_warn "未找到 pip3，将尝试使用 $PYTHON_BIN -m pip"
fi

# 检测 venv
if $PYTHON_BIN -c "import venv" 2>/dev/null; then
    log_pass "Python venv 模块可用"
else
    log_warn "Python venv 未安装，请执行: dnf install -y python3.12-venv"
fi

echo ""

# ---- 3. Node.js 环境 ----
echo -e "${BLUE}[3/9] Node.js 环境检测${NC}"

NODE_BIN=""
if command -v node &>/dev/null; then
    NODE_BIN="node"
    NODE_VER=$(node --version 2>&1 | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VER | cut -d. -f1)
    echo "  Node.js 路径: $(command -v node)"
    echo "  Node.js 版本: v$NODE_VER"

    if [ "$NODE_MAJOR" -ge 20 ]; then
        log_pass "Node.js >= 20 (v$NODE_VER)"
    elif [ "$NODE_MAJOR" -ge 18 ]; then
        log_warn "Node.js $NODE_VER 可用，推荐 >= 20"
    else
        log_fail "Node.js 版本过低 (v$NODE_VER)，需要 >= 20"
    fi
else
    log_fail "未找到 Node.js，请安装 Node.js 22 LTS"
    log_fail "安装方法: curl -fsSL https://rpm.nodesource.com/setup_22.x | bash - && dnf install -y nodejs"
fi

if command -v npm &>/dev/null; then
    NPM_VER=$(npm --version)
    echo "  npm 版本: v$NPM_VER"
    log_pass "npm 已安装 (v$NPM_VER)"
else
    log_fail "未找到 npm"
fi

echo ""

# ---- 4. 系统基础工具 ----
echo -e "${BLUE}[4/9] 系统基础工具检测${NC}"

TOOLS="curl wget git gcc make tar gzip"
for tool in $TOOLS; do
    if command -v $tool &>/dev/null; then
        VER=$($tool --version 2>&1 | head -1 | cut -c1-50)
        echo "  $tool: $VER"
        log_pass "$tool 已安装"
    else
        log_fail "$tool 未安装"
    fi
done

echo ""

# ---- 5. 网络连通性 ----
echo -e "${BLUE}[5/9] 网络连通性检测${NC}"

test_url() {
    local url=$1 name=$2
    if curl -s --connect-timeout 5 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -q '200\|301\|302'; then
        log_pass "$name ($url) 可访问"
    else
        log_warn "$name ($url) 无法访问（可能受防火墙限制）"
    fi
}

test_url "https://pypi.org" "PyPI"
test_url "https://registry.npmjs.org" "npm Registry"

echo ""

# ---- 6. 端口可用性 ----
echo -e "${BLUE}[6/9] 端口可用性检测${NC}"

check_port() {
    local port=$1 name=$2
    if ss -tln | grep -q ":$port "; then
        log_warn "端口 $port ($name) 已被占用"
        echo "        占用进程: $(ss -tlnp | grep ":$port " | awk '{print $NF}')"
    else
        log_pass "端口 $port ($name) 空闲"
    fi
}

check_port 8000 "后端 API"
check_port 3000 "前端 Vite Dev Server"

echo ""

# ---- 7. 系统资源 ----
echo -e "${BLUE}[7/9] 系统资源检测${NC}"

# 内存
MEM_TOTAL_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
if [ -n "$MEM_TOTAL_KB" ]; then
    MEM_TOTAL_MB=$((MEM_TOTAL_KB / 1024))
    echo "  总内存: ${MEM_TOTAL_MB}MB"
    if [ "$MEM_TOTAL_MB" -ge 2048 ]; then
        log_pass "内存 >= 2GB (${MEM_TOTAL_MB}MB)"
    elif [ "$MEM_TOTAL_MB" -ge 1024 ]; then
        log_warn "内存 ${MEM_TOTAL_MB}MB，建议 >= 2GB"
    else
        log_fail "内存不足 (${MEM_TOTAL_MB}MB)，需要 >= 2GB"
    fi
fi

# 磁盘
DISK_AVAIL_KB=$(df -k / 2>/dev/null | tail -1 | awk '{print $4}')
if [ -n "$DISK_AVAIL_KB" ]; then
    DISK_AVAIL_GB=$((DISK_AVAIL_KB / 1024 / 1024))
    echo "  可用磁盘 (/): ${DISK_AVAIL_GB}GB"
    if [ "$DISK_AVAIL_GB" -ge 10 ]; then
        log_pass "磁盘空间 >= 10GB (${DISK_AVAIL_GB}GB)"
    elif [ "$DISK_AVAIL_GB" -ge 5 ]; then
        log_warn "磁盘空间 ${DISK_AVAIL_GB}GB，建议 >= 10GB"
    else
        log_fail "磁盘空间不足 (${DISK_AVAIL_GB}GB)，需要 >= 5GB"
    fi
fi

# CPU
CPU_CORES=$(nproc 2>/dev/null)
echo "  CPU 核心数: $CPU_CORES"
if [ "$CPU_CORES" -ge 2 ]; then
    log_pass "CPU 核心数 >= 2"
else
    log_warn "CPU 核心数 $CPU_CORES，建议 >= 2"
fi

echo ""

# ---- 8. Python 依赖预检 ----
echo -e "${BLUE}[8/9] Python 依赖预检${NC}"

REQUIRED_PY_PKGS="fastapi uvicorn"
for pkg in $REQUIRED_PY_PKGS; do
    if $PYTHON_BIN -c "import $pkg" 2>/dev/null; then
        log_pass "Python 包 $pkg 已安装"
    else
        log_warn "Python 包 $pkg 未安装（将在部署时安装）"
    fi
done

echo ""

# ---- 9. 防火墙状态 ----
echo -e "${BLUE}[9/9] 防火墙检测${NC}"

if command -v firewall-cmd &>/dev/null; then
    if systemctl is-active --quiet firewalld 2>/dev/null; then
        echo "  firewalld 状态: 运行中"
        ACTIVE_ZONE=$(firewall-cmd --get-default-zone 2>/dev/null)
        echo "  默认区域: $ACTIVE_ZONE"

        for port in 8000 3000 80; do
            if firewall-cmd --list-ports 2>/dev/null | grep -q "$port"; then
                log_pass "端口 $port 已在防火墙开放"
            else
                log_warn "端口 $port 未在防火墙开放（开发模式建议临时关闭防火墙或开放端口）"
            fi
        done
    else
        log_pass "firewalld 未运行"
    fi
else
    log_warn "未检测到 firewalld"
fi

echo ""

# ---- 汇总 ----
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  检测结果汇总${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "  ${GREEN}通过: $PASS${NC}"
echo -e "  ${YELLOW}警告: $WARN${NC}"
echo -e "  ${RED}失败: $FAIL${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}  ✓ 环境检测通过，可以开始部署！${NC}"
    echo ""
    echo -e "${BLUE}  快速部署命令:${NC}"
    echo "  # 克隆项目（如果还没有）"
    echo "  git clone <repo-url> && cd AIOps-Platform/demo"
    echo ""
    echo "  # 一键安装并启动"
    echo "  bash scripts/setup-dev.sh"
    echo ""
    exit 0
else
    echo -e "${RED}  ✗ 环境检测未通过，请修复以上 ${FAIL} 个失败项后重试。${NC}"
    echo ""
    echo -e "${BLUE}  常见问题修复:${NC}"
    echo "  # 安装 Python 3.12"
    echo "  dnf install -y python3.12 python3.12-pip python3.12-devel"
    echo ""
    echo "  # 安装 Node.js 22"
    echo "  curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -"
    echo "  dnf install -y nodejs"
    echo ""
    echo "  # 安装基础工具"
    echo "  dnf install -y curl wget git gcc make"
    echo ""
    echo "  # 临时关闭防火墙（仅开发模式）"
    echo "  systemctl stop firewalld"
    echo ""
    exit 1
fi
