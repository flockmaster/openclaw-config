#!/bin/bash
# OpenClaw 自动备份脚本
# 每天凌晨 2 点自动提交并推送到 GitHub

set -e
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
OPENCLAW_DIR="$HOME/.openclaw"
WORKSPACE_DIR="$OPENCLAW_DIR/workspace"
LOG_FILE="$OPENCLAW_DIR/logs/backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 开始自动备份 ==="

# 备份主配置
log "备份主配置..."
cd "$OPENCLAW_DIR"

# 检查是否有变化
if ! git diff --quiet || ! git diff --cached --quiet; then
    git add -A
    git commit -m "Auto backup $DATE" || true
    if git push origin main 2>/dev/null; then
        log "主配置推送成功"
    else
        log "主配置推送失败，可能远程有更新，先 pull"
        git pull --rebase origin main || log "pull 失败，跳过本次推送"
        git push origin main || log "重试推送失败"
    fi
else
    log "主配置无变化，跳过"
fi

# 备份工作区
log "备份工作区..."
cd "$WORKSPACE_DIR"

# 切换到 workspace 分支
git checkout workspace 2>/dev/null || true

# 检查是否有变化
if ! git diff --quiet || ! git diff --cached --quiet; then
    git add -A
    git commit -m "Auto backup $DATE" || true
    if git push origin workspace 2>/dev/null; then
        log "工作区推送成功"
    else
        log "工作区推送失败，可能远程有更新，先 pull"
        git pull --rebase origin workspace || log "pull 失败，跳过本次推送"
        git push origin workspace || log "重试推送失败"
    fi
else
    log "工作区无变化，跳过"
fi

log "=== 备份完成 ==="
