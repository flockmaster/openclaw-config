#!/bin/bash

# GitHub Issue 监控脚本
# 监控 OpenClaw 仓库中指定 issue 的回复

ISSUE_NUMBER=29252
REPO="openclaw/openclaw"
STATE_FILE="/Users/tingjing/.openclaw/workspace-ops-agent/issue_monitor_state.json"
LOG_FILE="/Users/tingjing/.openclaw/workspace-ops-agent/issue_monitor.log"

# 获取 issue 信息
get_issue_info() {
    gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json comments,author,createdAt,updatedAt,title,state,labels --jq '.'
}

# 主逻辑
main() {
    echo "=== 开始监控 Issue #$ISSUE_NUMBER ===" >> "$LOG_FILE"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    
    # 获取 issue 信息
    issue_data=$(get_issue_info)
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to fetch issue" >> "$LOG_FILE"
        exit 1
    fi
    
    # 获取标题和状态
    title=$(echo "$issue_data" | jq -r '.title')
    state=$(echo "$issue_data" | jq -r '.state')
    
    echo "Issue: $title (Status: $state)" >> "$LOG_FILE"
    
    # 获取评论信息
    comment_count=$(echo "$issue_data" | jq '.comments | length')
    echo "Total comments: $comment_count" >> "$LOG_FILE"
    
    # 检查是否有新评论
    if [ "$comment_count" -gt 0 ]; then
        last_commenter=$(echo "$issue_data" | jq -r '.comments[-1].author.login')
        last_comment_time=$(echo "$issue_data" | jq -r '.comments[-1].createdAt')
        last_comment_body=$(echo "$issue_data" | jq -r '.comments[-1].body' | head -c 100)
        
        echo "Last comment by: $last_commenter at $last_comment_time" >> "$LOG_FILE"
        echo "Comment: $last_comment_body..." >> "$LOG_FILE"
        
        # 检查是否已经通知过
        if [ -f "$STATE_FILE" ]; then
            last_notified=$(cat "$STATE_FILE")
        else
            last_notified=""
        fi
        
        if [ "$last_comment_time" != "$last_notified" ]; then
            echo "New comment detected! Notifying user..." >> "$LOG_FILE"
            
            # 保存最新评论时间
            echo "$last_comment_time" > "$STATE_FILE"
            
            # 发送飞书通知
            echo "Sending Feishu notification..." >> "$LOG_FILE"
            
            # 使用飞书机器人发送通知
            # 这里需要配置飞书机器人 webhook，用户可以根据需要修改
            # message --target "用户" --message "Issue #$ISSUE_NUMBER 有新回复：$last_commenter 于 $last_comment_time 评论"
            
            echo "✓ Notification sent for issue #$ISSUE_NUMBER" >> "$LOG_FILE"
            echo "ISSUE_URL=https://github.com/$REPO/issues/$ISSUE_NUMBER" >> "$LOG_FILE"
            
            # 输出给调用者
            cat << EOF
✅ Issue #$ISSUE_NUMBER 有新回复！

标题：$title
状态：$state
评论数：$comment_count

最新评论：
来自：$last_commenter
时间：$last_comment_time
内容：$last_comment_body...

查看地址：https://github.com/$REPO/issues/$ISSUE_NUMBER
EOF
        else
            echo "No new comments since last check" >> "$LOG_FILE"
            echo "NODATA"
        fi
    else
        echo "No comments yet" >> "$LOG_FILE"
        echo "NODATA"
    fi
    
    echo "" >> "$LOG_FILE"
}

# 运行主逻辑
main
