#!/bin/bash
# AI 网关演示 — 启动/停止 mock 后端 + 网关
#
# 用法:
#   bash demo.sh start    # 启动两个 mock 后端 + 网关 (后台运行)
#   bash demo.sh stop     # 停止所有
#   bash demo.sh status   # 查看进程状态

DIR="$(cd "$(dirname "$0")" && pwd)"

start() {
    echo "=== 启动 AI 网关演示环境 ==="

    # 检查是否已在运行
    if pgrep -f "mock_vllm.py" > /dev/null 2>&1; then
        echo "[WARN] mock 后端已在运行, 先 stop 再 start"
        exit 1
    fi

    python3 "$DIR/mock_vllm.py" --port 8001 &
    python3 "$DIR/mock_vllm.py" --port 8002 &
    sleep 0.5

    python3 "$DIR/ai_gateway.py" &
    sleep 1

    echo ""
    echo "  mock 后端: http://localhost:8001, http://localhost:8002"
    echo "  AI 网关:   http://localhost:8080"
    echo ""
    echo "  测试命令:"
    echo "    curl -s http://localhost:8080/health"
    echo "    curl -s http://localhost:8080/v1/chat/completions \\"
    echo "      -H 'Content-Type: application/json' \\"
    echo "      -H 'Authorization: Bearer test-key' \\"
    echo "      -d '{\"model\":\"test\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}'"
    echo ""
    echo "  停止: bash demo.sh stop"
}

stop() {
    echo "=== 停止 AI 网关演示环境 ==="
    pkill -f "mock_vllm.py" 2>/dev/null && echo "[OK] mock 后端 已停止" || echo "[--] mock 后端 未在运行"
    pkill -f "ai_gateway.py" 2>/dev/null && echo "[OK] AI 网关 已停止"   || echo "[--] AI 网关 未在运行"
}

status() {
    echo "=== AI 网关演示环境 状态 ==="
    echo -n "  mock 后端 (8001): "; pgrep -f "mock_vllm.py.*8001" > /dev/null 2>&1 && echo "运行中" || echo "未运行"
    echo -n "  mock 后端 (8002): "; pgrep -f "mock_vllm.py.*8002" > /dev/null 2>&1 && echo "运行中" || echo "未运行"
    echo -n "  AI 网关 (8080):   "; pgrep -f "ai_gateway.py" > /dev/null 2>&1 && echo "运行中" || echo "未运行"
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "  /health: OK"
    else
        echo "  /health: 无法连接"
    fi
}

case "${1:-start}" in
    start)  start ;;
    stop)   stop ;;
    status) status ;;
    *)      echo "用法: bash demo.sh {start|stop|status}" ;;
esac
