#!/bin/bash
# OpenClaw 配置恢复脚本
# 用法：./restore-from-git.sh [commit-hash|branch|tag]

set -e

OPENCLAW_DIR="$HOME/.openclaw"
WORKSPACE_DIR="$OPENCLAW_DIR/workspace"

echo "=== OpenClaw 配置恢复 ==="
echo "目标目录：$OPENCLAW_DIR"

# 检查 Git 仓库
if [ ! -d "$OPENCLAW_DIR/.git" ]; then
    echo "错误：主配置目录不是 Git 仓库"
    exit 1
fi

if [ ! -d "$WORKSPACE_DIR/.git" ]; then
    echo "错误：工作区目录不是 Git 仓库"
    exit 1
fi

# 恢复主配置
echo ""
echo "1. 恢复主配置..."
cd "$OPENCLAW_DIR"
if [ -n "$1" ]; then
    echo "   恢复到：$1"
    git checkout "$1" -- openclaw.json .env credentials/ agents/main/ 2>/dev/null || {
        echo "   警告：部分文件恢复失败"
    }
else
    echo "   恢复到最新"
    git checkout HEAD -- openclaw.json .env credentials/ agents/main/ 2>/dev/null || {
        echo "   警告：部分文件恢复失败"
    }
fi

# 恢复工作区
echo ""
echo "2. 恢复工作区..."
cd "$WORKSPACE_DIR"
if [ -n "$1" ]; then
    echo "   恢复到：$1"
    git checkout "$1" -- . 2>/dev/null || {
        echo "   警告：部分文件恢复失败"
    }
else
    echo "   恢复到最新"
    git checkout HEAD -- . 2>/dev/null || {
        echo "   警告：部分文件恢复失败"
    }
fi

# 修复权限
echo ""
echo "3. 修复敏感文件权限..."
chmod 600 "$OPENCLAW_DIR/.env" 2>/dev/null || true
chmod 600 "$OPENCLAW_DIR/credentials/"* 2>/dev/null || true

# 检查状态
echo ""
echo "4. 当前状态："
cd "$OPENCLAW_DIR"
echo "   主配置：$(git log --oneline -1)"
cd "$WORKSPACE_DIR"
echo "   工作区：$(git log --oneline -1)"

echo ""
echo "=== 恢复完成 ==="
echo "重启 Gateway: openclaw gateway restart"
