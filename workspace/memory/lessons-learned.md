# 血泪教训

> 2026-02-27 凌晨复盘

## 多智能体协同

1. **spawn 必须带 agentId** — 不带就是分配给自己，等于没分配
2. **超时要重试不要甩锅** — 我是监督者，负责任务完成，不是传话筒
3. **结果回来立刻行动** — sub-agent 完成后立刻执行下一步，不等用户催
4. **验证产物再汇报** — sub-agent 说完成了要检查文件是否存在、内容是否正确
5. **跨 agent 路径问题** — 不同 agent 的 workspace 不同，派任务时必须写绝对路径

## 承诺与执行

6. **说到必须做到** — 说"我会监控"就建 cron，说"交出去"就 spawn，没有第三种选项

## Cron 与会话

7. **isolated cron 没有主会话上下文** — 监督类 cron 要设计退出机制（如检查标记文件）
8. **sub-agent 完成后 main 不会自动给用户发消息** — 需要心跳或用户触发

## 安全与操作

9. **大任务容易超时** — 要用规划模式拆成小任务
10. **删目录前必须确认** — workspaceq 事件：以为是拼写错误就删了，结果是真正的安装路径
11. **改配置前必须查文档** — 2026-03-02 事件：加了 `web.search` 配置项，OpenClaw 新版本不认，配置无效导致系统崩溃。改动后必须重启验证
12. **OpenClaw 配置文档地址** — `https://docs.openclaw.ai/llms.txt`，修改任何 OpenClaw 配置前必须先查阅此文档，确认配置项是否被支持

## 技能开发

13. **Skill 文档要写实践经验** — 跑通后立刻更新 SKILL.md，包括：踩过的坑、实际用的依赖版本、缓存路径、预下载命令
14. **抖音 skill 用 openai-whisper** — faster-whisper 模型下载有问题，改用 openai-whisper（`pip install openai-whisper`）
15. **Whisper 模型缓存** — `~/.cache/whisper/`，建议用 `python3 -c "import whisper; whisper.load_model('small')"` 预下载

## 权限

- 有权创建新 agent，按需创建，不再请示
