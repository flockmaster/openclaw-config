#!/bin/bash
# Gateway Watchdog Script v2 - 智能版（带 Codex 自动修复）
# 使用方法：./gateway-watchdog-v2.sh start

set -e

LOG_DIR="$HOME/.openclaw/logs"
ERR_LOG="$LOG_DIR/gateway.err.log"
WATCHDOG_LOG="$LOG_DIR/watchdog-v2.log"
PID_FILE="$HOME/.openclaw/watchdog-v2.pid"
LOCK_FILE="$HOME/.openclaw/watchdog-v2.lock"
CONFIG_FILE="$HOME/.openclaw/openclaw.json"
CONFIG_BACKUP_DIR="$HOME/.openclaw/config-backups"

# 配置
HEALTH_CHECK_INTERVAL=10    # 健康检查间隔（秒）
MAX_RESTART_ATTEMPTS=3      # 最大重启尝试次数
GATEWAY_PORT=18789

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# 检查单实例
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

# 备份配置
backup_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log "WARN" "配置文件不存在：$CONFIG_FILE"
        return 1
    fi
    
    mkdir -p "$CONFIG_BACKUP_DIR"
    local backup_file="$CONFIG_BACKUP_DIR/openclaw.$(date +%Y%m%d%H%M%S).json"
    cp "$CONFIG_FILE" "$backup_file"
    log "INFO" "配置已备份：$backup_file"
    
    # 保留最近 10 个备份
    ls -t "$CONFIG_BACKUP_DIR"/*.json 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    
    return 0
}

# 检查 Gateway 是否在运行
is_gateway_running() {
    if lsof -i :$GATEWAY_PORT >/dev/null 2>&1; then
        return 0
    fi
    if pgrep -f "openclaw-gateway" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# 获取 Gateway PID
get_gateway_pid() {
    lsof -t -i :$GATEWAY_PORT 2>/dev/null | head -1
}

# 停止 Gateway
stop_gateway() {
    log "INFO" "正在停止 Gateway..."
    
    local pid=$(get_gateway_pid)
    if [ -n "$pid" ]; then
        kill -TERM "$pid" 2>/dev/null || true
        sleep 2
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        log "INFO" "Gateway 已停止 (PID: $pid)"
    fi
    
    pkill -f "openclaw-gateway" 2>/dev/null || true
    sleep 1
}

# 启动 Gateway
start_gateway() {
    log "INFO" "正在启动 Gateway..."
    
    cd "$HOME/.npm-global/lib/node_modules/openclaw" || return 1
    
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

# 调用 Codex 诊断修复
codex_diagnose_and_fix() {
    log "INFO" "=== 调用 Codex 诊断修复 ==="
    
    # 收集错误日志最后 200 行
    local error_snippet=""
    if [ -f "$ERR_LOG" ]; then
        error_snippet=$(tail -200 "$ERR_LOG" 2>/dev/null | head -100)
    fi
    
    # 收集当前配置
    local config_snippet=""
    if [ -f "$CONFIG_FILE" ]; then
        config_snippet=$(cat "$CONFIG_FILE" 2>/dev/null | head -200)
    fi
    
    # 写诊断请求到临时文件
    local diagnosis_request="$LOG_DIR/codex_diagnosis_request.txt"
    cat > "$diagnosis_request" << EOF
OpenClaw Gateway 启动失败，请帮我诊断并修复问题。

## 错误日志（最后 200 行中的前 100 行）
$error_snippet

## 当前配置（前 200 行）
$config_snippet

## 任务
1. 分析错误原因
2. 如果是配置文件问题（JSON 格式错误、无效配置项等），直接修复 ~/.openclaw/openclaw.json
3. 如果是其他问题，尝试自动修复
4. 修复后验证配置是否有效

注意：修改配置前已备份，修复失败可以回滚。
EOF

    log "INFO" "诊断请求已写入：$diagnosis_request"
    
    # 调用 Codex
    cd "$HOME/.openclaw/workspace" || return 1
    
    log "INFO" "Codex 开始诊断..."
    
    # 使用 Codex CLI 执行诊断
    if command -v codex >/dev/null 2>&1; then
        # 执行诊断，超时 5 分钟
        if command -v timeout >/dev/null 2>&1; then
            TIMEOUT_CMD="timeout"
        elif command -v gtimeout >/dev/null 2>&1; then
            TIMEOUT_CMD="gtimeout"
        else
            log "ERROR" "未找到 timeout 或 gtimeout 命令(请通过 brew install coreutils 安装)"
            return 1
        fi
        
        $TIMEOUT_CMD 300 codex exec --full-auto "OpenClaw Gateway 启动失败，请诊断并修复。诊断请求在 ~/.openclaw/logs/codex_diagnosis_request.txt，修复后返回修复结果说明" 2>&1 | tee "$LOG_DIR/codex_output.log"
        
        local exit_code=${PIPESTATUS[0]}
        
        if [ $exit_code -eq 0 ]; then
            log "INFO" "Codex 诊断完成"
            return 0
        elif [ $exit_code -eq 124 ]; then
            log "WARN" "Codex 诊断超时（>5 分钟）"
            return 1
        else
            log "ERROR" "Codex 诊断失败（退出码：$exit_code）"
            return 1
        fi
    else
        log "ERROR" "未找到 codex 命令"
        return 1
    fi
}

# 回滚配置
rollback_config() {
    log "INFO" "正在回滚配置..."
    
    if [ ! -d "$CONFIG_BACKUP_DIR" ]; then
        log "WARN" "没有备份目录"
        return 1
    fi
    
    local latest_backup=$(ls -t "$CONFIG_BACKUP_DIR"/*.json 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        log "WARN" "没有找到备份文件"
        return 1
    fi
    
    cp "$latest_backup" "$CONFIG_FILE"
    log "INFO" "配置已回滚到：$latest_backup"
    return 0
}

# 主修复流程
attempt_repair() {
    log "WARN" "=== Gateway 启动失败，开始修复流程 ==="
    
    # 步骤 1: 备份当前配置
    backup_config
    
    # 步骤 2: 尝试简单重启
    log "INFO" "尝试简单重启 (1/$MAX_RESTART_ATTEMPTS)..."
    if start_gateway; then
        log "INFO" "简单重启成功"
        return 0
    fi
    
    # 步骤 3: 调用 Codex 诊断修复
    log "INFO" "简单重启失败，调用 Codex 诊断..."
    if codex_diagnose_and_fix; then
        log "INFO" "Codex 诊断完成，尝试重启..."
        
        # 清理错误日志避免误判
        if [ -f "$ERR_LOG" ]; then
            mv "$ERR_LOG" "${ERR_LOG}.bak.$(date +%Y%m%d%H%M%S)"
        fi
        
        if start_gateway; then
            log "INFO" "Codex 修复后重启成功"
            return 0
        else
            log "WARN" "Codex 修复后重启仍失败，回滚配置"
            rollback_config
        fi
    else
        log "WARN" "Codex 诊断失败"
    fi
    
    # 步骤 4: 放弃
    log "ERROR" "=== 修复失败，放弃等待 ==="
    return 1
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
    log "INFO" "=== Watchdog v2 启动 (PID: $$) ==="
    log "INFO" "监控配置：检查间隔=${HEALTH_CHECK_INTERVAL}s, 最大重启尝试=$MAX_RESTART_ATTEMPTS"
    log "INFO" "配置备份目录：$CONFIG_BACKUP_DIR"
    
    local consecutive_failures=0
    
    while true; do
        if ! health_check; then
            consecutive_failures=$((consecutive_failures + 1))
            log "WARN" "Gateway 检查失败 (连续 $consecutive_failures 次)"
            
            if [ $consecutive_failures -ge 2 ]; then
                # 尝试修复
                if attempt_repair; then
                    consecutive_failures=0
                else
                    # 修复失败，停止尝试，等待下次检查
                    log "INFO" "本次修复失败，等待下次检查..."
                    consecutive_failures=0
                fi
            fi
        else
            consecutive_failures=0
        fi
        
        sleep $HEALTH_CHECK_INTERVAL
    done
}

# 命令行参数
case "${1:-}" in
    start)
        check_single_instance
        mkdir -p "$CONFIG_BACKUP_DIR"
        main_loop
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            pid=$(cat "$PID_FILE")
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
            pid=$(cat "$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                echo "Watchdog v2 运行中 (PID: $pid)"
                exit 0
            fi
        fi
        echo "Watchdog v2 未运行"
        exit 1
        ;;
    backup)
        backup_config
        ;;
    *)
        echo "用法：$0 {start|stop|status|backup}"
        exit 1
        ;;
esac
