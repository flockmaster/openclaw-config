#!/bin/bash
# Gateway Watchdog Script - 监控并防止 Gateway 重启循环
# 使用方法：./gateway-watchdog.sh &

set -e

LOG_DIR="$HOME/.openclaw/logs"
ERR_LOG="$LOG_DIR/gateway.err.log"
WATCHDOG_LOG="$LOG_DIR/watchdog.log"
PID_FILE="$HOME/.openclaw/watchdog.pid"
LOCK_FILE="$HOME/.openclaw/watchdog.lock"

# 配置
MAX_RESTART_ATTEMPTS=5      # 允许的最大重启尝试次数（在时间窗口内）
TIME_WINDOW_SECONDS=60      # 时间窗口（秒）
HEALTH_CHECK_INTERVAL=10    # 健康检查间隔（秒）
GATEWAY_PORT=18789
GATEWAY_URL="ws://127.0.0.1:$GATEWAY_PORT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $msg" >> "$WATCHDOG_LOG"
    
    case "$level" in
        ERROR) echo -e "${RED}[$timestamp] [$level] $msg${NC}" ;;
        WARN)  echo -e "${YELLOW}[$timestamp] [$level] $msg${NC}" ;;
        INFO)  echo -e "${GREEN}[$timestamp] [$level] $msg${NC}" ;;
        *)     echo "[$timestamp] [$level] $msg" ;;
    esac
}

# 检查是否已有 watchdog 在运行
check_single_instance() {
    if [ -f "$LOCK_FILE" ]; then
        local old_pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            log "INFO" "Watchdog 已在运行 (PID: $old_pid)"
            exit 0
        else
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
    trap "rm -f $LOCK_FILE $PID_FILE" EXIT
}

# 检查 Gateway 是否在运行
is_gateway_running() {
    # 方法 1: 检查端口
    if lsof -i :$GATEWAY_PORT >/dev/null 2>&1; then
        return 0
    fi
    
    # 方法 2: 检查进程
    if pgrep -f "openclaw-gateway" >/dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

# 检查日志中是否有重启循环模式
check_restart_loop() {
    if [ ! -f "$ERR_LOG" ]; then
        return 1
    fi
    
    # 统计最近 TIME_WINDOW_SECONDS 秒内的重启尝试次数
    local cutoff=$(date -v-"${TIME_WINDOW_SECONDS}S" '+%Y-%m-%dT%H:%M' 2>/dev/null || date -d "-${TIME_WINDOW_SECONDS} seconds" '+%Y-%m-%dT%H:%M' 2>/dev/null)
    
    if [ -z "$cutoff" ]; then
        # 如果日期计算失败，用简单方法：检查最后 N 行
        local count=$(tail -100 "$ERR_LOG" 2>/dev/null | grep -c "Gateway failed to start" || echo 0)
        if [ "$count" -ge "$MAX_RESTART_ATTEMPTS" ]; then
            return 0
        fi
    else
        local count=$(grep "$cutoff" "$ERR_LOG" 2>/dev/null | grep -c "Gateway failed to start" || echo 0)
        if [ "$count" -ge "$MAX_RESTART_ATTEMPTS" ]; then
            return 0
        fi
    fi
    
    return 1
}

# 获取 Gateway PID
get_gateway_pid() {
    lsof -t -i :$GATEWAY_PORT 2>/dev/null | head -1
}

# 优雅地停止 Gateway
stop_gateway() {
    log "INFO" "正在停止 Gateway..."
    
    local pid=$(get_gateway_pid)
    if [ -n "$pid" ]; then
        kill -TERM "$pid" 2>/dev/null || true
        sleep 2
        
        # 如果还没停，强制杀掉
        if kill -0 "$pid" 2>/dev/null; then
            log "WARN" "Gateway 未响应 TERM 信号，发送 KILL"
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        log "INFO" "Gateway 已停止 (PID: $pid)"
    else
        log "WARN" "未找到 Gateway 进程"
    fi
    
    # 清理可能的残留
    pkill -f "openclaw-gateway" 2>/dev/null || true
    sleep 1
}

# 启动 Gateway
start_gateway() {
    log "INFO" "正在启动 Gateway..."
    
    cd "$HOME/.npm-global/lib/node_modules/openclaw" || return 1
    
    # 使用 openclaw gateway start 命令
    if command -v openclaw >/dev/null 2>&1; then
        openclaw gateway start >/dev/null 2>&1 &
        sleep 3
        
        if is_gateway_running; then
            log "INFO" "Gateway 启动成功"
            return 0
        else
            log "ERROR" "Gateway 启动失败"
            return 1
        fi
    else
        log "ERROR" "未找到 openclaw 命令"
        return 1
    fi
}

# 健康检查
health_check() {
    if is_gateway_running; then
        local pid=$(get_gateway_pid)
        log "DEBUG" "Gateway 运行中 (PID: $pid)"
        return 0
    else
        log "WARN" "Gateway 未运行"
        return 1
    fi
}

# 主循环
main_loop() {
    echo $$ > "$PID_FILE"
    log "INFO" "=== Watchdog 启动 (PID: $$) ==="
    log "INFO" "监控配置：最大重启尝试=$MAX_RESTART_ATTEMPTS, 时间窗口=${TIME_WINDOW_SECONDS}s, 检查间隔=${HEALTH_CHECK_INTERVAL}s"
    
    local consecutive_failures=0
    local max_consecutive_failures=3
    
    while true; do
        # 检查重启循环
        if check_restart_loop; then
            log "ERROR" "检测到 Gateway 重启循环！开始修复..."
            
            # 停止 Gateway
            stop_gateway
            
            # 清理错误日志（避免误报）
            if [ -f "$ERR_LOG" ]; then
                local backup="${ERR_LOG}.bak.$(date +%Y%m%d%H%M%S)"
                mv "$ERR_LOG" "$backup"
                log "INFO" "错误日志已备份到 $backup"
            fi
            
            # 等待一小段时间
            sleep 2
            
            # 启动 Gateway
            if start_gateway; then
                log "INFO" "Gateway 重启完成"
                consecutive_failures=0
            else
                log "ERROR" "Gateway 重启失败"
                consecutive_failures=$((consecutive_failures + 1))
            fi
        else
            # 正常健康检查
            if ! health_check; then
                consecutive_failures=$((consecutive_failures + 1))
                
                if [ $consecutive_failures -ge $max_consecutive_failures ]; then
                    log "ERROR" "Gateway 连续 $consecutive_failures 次检查失败，尝试重启..."
                    
                    if start_gateway; then
                        consecutive_failures=0
                    fi
                else
                    log "WARN" "Gateway 检查失败 ($consecutive_failures/$max_consecutive_failures)"
                fi
            else
                consecutive_failures=0
            fi
        fi
        
        sleep $HEALTH_CHECK_INTERVAL
    done
}

# 命令行参数
case "${1:-}" in
    start)
        check_single_instance
        main_loop
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                log "INFO" "Watchdog 已停止"
            fi
            rm -f "$PID_FILE" "$LOCK_FILE"
        else
            log "WARN" "Watchdog 未运行"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                echo "Watchdog 运行中 (PID: $pid)"
                exit 0
            fi
        fi
        echo "Watchdog 未运行"
        exit 1
        ;;
    *)
        echo "用法：$0 {start|stop|status}"
        exit 1
        ;;
esac
