#!/bin/bash
# ============================================================
# AIOps Demo — 服务管理脚本
# 用法: bash service.sh {start|stop|restart|status|log}
# ============================================================

set -e

DEMO_DIR="/opt/demo"
VENV_DIR="$DEMO_DIR/.venv"
BACKEND_DIR="$DEMO_DIR/backend"
LOG_FILE="$DEMO_DIR/backend.log"
PID_FILE="$DEMO_DIR/backend.pid"
PORT=8000

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

get_pid() {
    ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1
}

# ---- 启动 ----
do_start() {
    echo -e "${BLUE}启动 AIOps Demo 服务...${NC}"

    # 检查是否已运行
    PID=$(get_pid)
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}服务已在运行 (PID: $PID, 端口: $PORT)${NC}"
        echo -e "访问地址: ${GREEN}http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
        return 0
    fi

    # 激活虚拟环境并启动
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"

    nohup uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info > "$LOG_FILE" 2>&1 &
    NEW_PID=$!
    echo $NEW_PID > "$PID_FILE"

    sleep 2

    # 验证启动
    if kill -0 $NEW_PID 2>/dev/null; then
        echo -e "${GREEN}✓ 服务启动成功!${NC}"
        echo -e "  PID:     $NEW_PID"
        echo -e "  端口:    $PORT"
        echo -e "  前端:    ${GREEN}http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
        echo -e "  API 文档: http://$(hostname -I | awk '{print $1}'):$PORT/api/docs"
        echo -e "  日志:    $LOG_FILE"
    else
        echo -e "${RED}✗ 启动失败，请查看日志: tail -20 $LOG_FILE${NC}"
        return 1
    fi
}

# ---- 停止 ----
do_stop() {
    echo -e "${BLUE}停止 AIOps Demo 服务...${NC}"

    PID=$(get_pid)
    if [ -z "$PID" ]; then
        echo -e "${YELLOW}服务未运行${NC}"
        rm -f "$PID_FILE"
        return 0
    fi

    kill $PID 2>/dev/null
    sleep 1

    # 如果未退出，强制杀死
    if kill -0 $PID 2>/dev/null; then
        kill -9 $PID 2>/dev/null
        sleep 1
    fi

    if kill -0 $PID 2>/dev/null; then
        echo -e "${RED}✗ 无法停止进程 $PID${NC}"
        return 1
    else
        echo -e "${GREEN}✓ 服务已停止 (PID: $PID)${NC}"
        rm -f "$PID_FILE"
    fi
}

# ---- 重启 ----
do_restart() {
    do_stop
    sleep 1
    do_start
}

# ---- 状态 ----
do_status() {
    PID=$(get_pid)
    SERVER_IP=$(hostname -I | awk '{print $1}')

    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}  AIOps Demo 服务状态${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"

    if [ -n "$PID" ]; then
        echo -e "  状态:     ${GREEN}运行中${NC}"
        echo -e "  PID:      $PID"
        echo -e "  端口:     $PORT"

        # CPU/内存
        CPU_MEM=$(ps -p $PID -o %cpu,%mem,etime --no-headers 2>/dev/null)
        echo -e "  资源:     $CPU_MEM"

        # 健康检查
        HEALTH=$(curl -s http://localhost:$PORT/api/health 2>/dev/null)
        if [ -n "$HEALTH" ]; then
            echo -e "  健康检查: ${GREEN}$HEALTH${NC}"
        else
            echo -e "  健康检查: ${RED}无响应${NC}"
        fi

        echo -e "  前端地址: ${GREEN}http://$SERVER_IP:$PORT${NC}"
        echo -e "  API 文档: http://$SERVER_IP:$PORT/api/docs"
        echo -e "  日志文件: $LOG_FILE"
    else
        echo -e "  状态:     ${RED}未运行${NC}"
    fi
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
}

# ---- 日志 ----
do_log() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}最近 30 行日志 ($LOG_FILE):${NC}"
        echo -e "${BLUE}───────────────────────────────────────${NC}"
        tail -30 "$LOG_FILE"
    else
        echo -e "${YELLOW}日志文件不存在${NC}"
    fi
}

# ============================================
case "${1:-status}" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_restart ;;
    status)  do_status ;;
    log)     do_log ;;
    *)
        echo "用法: bash service.sh {start|stop|restart|status|log}"
        echo ""
        echo "  start    — 启动服务"
        echo "  stop     — 停止服务"
        echo "  restart  — 重启服务"
        echo "  status   — 查看服务状态"
        echo "  log      — 查看最近日志"
        exit 1
        ;;
esac
