# TOOLS.md - 工具配置笔记

## 凭据位置

凭据存 `.credentials/`（gitignore）：
- `example-api.txt` — 示例 API Key

## 搜索引擎偏好

**优先使用 Tavily 搜索**，不用 Brave web_search。

```bash
python3 /Users/tingjing/.openclaw/workspace/skills/openclaw-tavily-search/scripts/tavily_search.py --query "..." --max-results 5 --format md
```

API Key 已配置在 `~/.openclaw/.env`

## 本地 AI 工具（后援团队）

**可用工具：**
- `codex` — OpenAI Codex CLI
- `claudecode` — Anthropic Claude Code CLI
- `Antigravity` — （待补充具体用途）

**调用方式：**
```bash
# Claude Code 全自动模式（跳过权限确认）
claude --dangerously-skip-permissions

# 或者进入后使用 YOLO 模式
claude
/yolo
```

**使用场景：**
- 复杂开发任务 → 可 spawn 子 agent 调用这些工具
- 需要更强编码能力时 → 委派给 Codex/Claude Code
- 18 号是调度员，不是执行者——能派给后援的就派

**注意：**
- 这些工具在用户本地 Mac 上运行
- 调用需要确保终端环境可用
- 全自动模式（--dangerously-skip-permissions / /yolo）慎用，确保任务安全

---

## 备份与恢复机制

### Happy 手机端（复活甲）

**用途：** 当 18 号挂掉时，通过 Happy 控制 Claude 唤醒 18 号

**恢复流程：**
1. 检测到 18 号无响应（心跳停止/会话超时）
2. 用户通过 Happy 手机端 → 唤醒 Claude
3. Claude → 重启 OpenClaw Gateway / 恢复会话

**注意：**
- Happy 是手机端应用（具体配置待补充）
- 这是最后的恢复手段，优先尝试自动恢复（心跳重试）
- 用户需要知道触发条件：什么时候算"18 号挂了"

### 自动恢复（优先）

**第一层：Watchdog v2**
- 脚本：`~/.openclaw/scripts/gateway-watchdog-v2.sh`
- 检查频率：每 10 秒
- 日志：`~/.openclaw/logs/watchdog-v2.log`
- 动作：Gateway 崩溃 → 自动重启

**第二层：心跳机制**
- 频率：30 分钟（有活跃任务时 5 分钟）
- 检查项：sub-agent 状态、错误日志、任务进度
- 记录：`memory/heartbeat-state.json`

**第三层：手动恢复**
- Happy 手机端 → Claude → 唤醒 18 号
- 用户命令：`/new` 或 `/reset` 重置会话

## 工具配置项

- 工具设置和配置
- 凭据位置（**不存实际凭据**！）
- 已发现的问题和解决办法
- 常用命令和模式
- 集成注意点

## 为什么单独定义？

Skills 定义**工具怎么工作**；这个文件记录**你的配置**——独特于你环境的细节。

---

*加任何帮你干活的笔记。这就是你的作弊小抄。*
