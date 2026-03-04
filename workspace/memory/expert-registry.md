# 专家注册索引

> 本文件供 main agent 路由决策时查阅。expert-scout 引入新专家后会自动更新。

## 自建团队

| agentId | 名称 | 领域 | 擅长 | 模型 | 飞书群 |
|---------|------|------|------|------|--------|
| `frontend-engineer` | 前端工程师 | 前端开发 | React/Vue/Flutter、UI/UX 实现、组件化、响应式、性能优化 | kimi-k2.5 | 技术开发群 |
| `backend-engineer` | 后端工程师 | 后端开发 | API 设计、数据库、系统架构、安全、Python/Go/Java | qwen3.5-plus | — |
| `product-manager` | 产品经理 | 产品设计 | PRD 撰写、需求分析、竞品分析、用户研究、功能规划 | qwen3.5-plus | 产品讨论群 |
| `math-teacher` | 数学老师 | 数学教育 | 小学数学教学（汐汐专属）、出题、错题复习、自适应难度 | kimi-k2.5 | 数学学习群 |
| `ops-agent` | 运维专家 | 运维/DevOps | 部署、CI/CD、监控告警、安全加固、备份恢复 | glm-5 | — |
| `qa-engineer` | QA 测试 | 质量保障 | 文件验证、脚本测试、API 测试、集成测试、回归测试 | glm-5 | — |
| `gpt5-tester` | 模型测试专家 | AI 评测 | 模型对比、测试用例设计、多维度评分、结构化报告 | qwen3.5-plus | — |

## 引入专家（来自开源社区）

<!-- BEGIN IMPORTED EXPERTS -->
<!-- expert-scout 引入后自动填充此区域 -->
<!-- 格式：| `agent-id` | 名称 | 领域 | 来源 | 验证状态 | 引入时间 | -->
| `data-analysis-expert` | 数据分析专家 | 数据分析/BI/统计 | github (System-Prompt-Library) | adapted | 2026-03-02 |
<!-- END IMPORTED EXPERTS -->

## 领域覆盖

### 已覆盖
- [x] 前端开发（frontend-engineer）
- [x] 后端开发（backend-engineer）
- [x] 产品设计（product-manager）
- [x] 测试 QA（qa-engineer）
- [x] 运维 DevOps（ops-agent）
- [x] AI 模型评测（gpt5-tester）
- [x] 数学教育（math-teacher）

### 缺口（按需引入）
- [ ] 数据分析 / BI
- [ ] UI/UX 设计（独立设计师，不只是前端实现）
- [ ] 安全审计
- [ ] 技术文档 / 技术写作
- [ ] 项目管理 / 敏捷教练
- [ ] 数据库 DBA（深度优化，超出后端工程师范围时）
