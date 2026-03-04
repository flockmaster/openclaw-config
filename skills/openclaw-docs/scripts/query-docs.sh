#!/bin/bash
# OpenClaw 文档查询脚本

QUERY="$1"
MAX="$2"

if [ -z "$QUERY" ]; then
    echo "用法: $0 <关键词> [最大字符数]"
    echo "示例: $0 cron 5000"
    exit 1
fi

MAX=${MAX:-8000}

# 1. 获取文档索引并匹配
INDEX_URL="https://docs.openclaw.ai/llms.txt"
DOCS=$(curl -s "$INDEX_URL" | grep -i "$QUERY")

if [ -z "$DOCS" ]; then
    echo "未找到匹配 '$QUERY' 的文档"
    exit 1
fi

echo "=== 匹配到的文档 ==="
echo "$DOCS"
echo ""

# 2. 提取第一个匹配的文档链接
FIRST_LINK=$(echo "$DOCS" | head -1 | grep -o 'https://[^)]*\.md' | head -1)

if [ -n "$FIRST_LINK" ]; then
    echo "=== 读取文档: $FIRST_LINK ==="
    curl -s "$FIRST_LINK" | head -200
else
    echo "无法提取文档链接"
    exit 1
fi