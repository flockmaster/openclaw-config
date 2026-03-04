# AGENTS.md - 任务分配规则

## 可用子 Agent

- **backend-engineer** - 代码开发、API 设计、数据库任务
- **frontend-engineer** - UI 实现、组件开发、交互优化
- **qa-engineer** - 测试验证、自动化测试、质量检查

## 任务分配原则

1. 测试准备阶段：自担任务拆解，需要代码开发时委托 @backend-engineer
2. 测试执行阶段：需要 UI 交互时委托 @frontend-engineer
3. Bug 验证阶段：委托 @qa-engineer 进行回归测试

## 当前 Agent 职责

GPT-5 测试专家，专注模型功能、性能、安全性测试。
