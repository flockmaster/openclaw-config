# 模型分配与降级策略

> 2026-02-27 更新

## Agent 模型配置

| Agent | 首选模型 | 降级模型 | 适用场景 |
|-------|---------|---------|---------|
| frontend-engineer | gemini-3-1-pro | kimi-k2.5 → qwen3-coder-plus | 前端开发、UI、组件 |
| backend-engineer | gpt-5.3-codex | glm-5 → qwen3-coder-plus | 后端开发、API、数据库 |
| product-manager | opus-4.6 | qwen3-coder-plus → glm-5 | 产品设计、需求分析 |
| math-teacher | kimi-k2.5 | qwen3-coder-plus → glm-5 | 数学教学、题目解答 |
| ops-agent | qwen3-coder-plus | glm-5 | 运维、文件处理、下载 |
| qa-engineer | qwen3-coder-plus | glm-5 | 测试、验证 |
| 研究任务 | gemini-3-1-pro | kimi-k2.5 | 复杂分析、调研 |

## 降级规则

首选模型失败 → 自动切换降级模型 → 全部失败才报错

## 兼容性测试结果（2026-02-27）

| 模型 | Provider API | 简单任务 | 大任务 | 备注 |
|------|-------------|---------|--------|------|
| qwen3-coder-plus | openai-completions | OK | OK | 唯一完全可靠 |
| gpt-5.3-codex | openai-responses | OK | 超时 | 小任务 OK，大任务 timeout |
| gemini-3-1-pro | openai-completions (local proxy) | 不稳定 | 失败 | 本地代理不稳定 |
| kimi-k2.5 | openai-completions | 失败 | 失败 | 疑似 auth.json default_profile 干扰 |

## Key Decisions

- 心跳默认 30 分钟，有活跃任务时缩短到 5 分钟
- thinking 默认 high
- 子智能体超时时间 600 秒（10 分钟）
- 任务颗粒度：原子任务 ≤ 5 分钟执行，≤ 100 行代码
- 子智能体必须自验证：检查产物存在、大小、内容
