# 骨架驱动 TDD 工作流 — 实现计划

> 来源：`notes/agent_experts_architecture_planning.md` Section 四
> 前置工作：Phase 1-2（专家注册 + 路由 + expert-scout）已于 2026-03-02 完成
> 目标：在 OpenClaw 多智能体体系中落地标准化开发流程

---

## 背景与前置成果

### 已完成（2026-03-02）

1. **main agent SOUL.md 增强** — 加入分配铁律（含 gpt5-tester）、引入专家区、三级路由决策
2. **expert-registry.md** — 专家索引，含 7 个自建 + 1 个引入专家（data-analysis-expert）
3. **expert-scout Skill** — 多来源专家猎头，已验证 GitHub 仓库为最佳来源，本地 prompt-library 已下载
4. **EXPERT-META.md 规范** — 专家"身份证"模板
5. **端到端验证** — 从 System-Prompt-Library 引入 Data Trends Identifier 为数据分析专家，全流程跑通

### 相关文件位置

| 文件 | 路径 |
|------|------|
| 架构规划原文 | `~/.openclaw/workspace/notes/agent_experts_architecture_planning.md` |
| Phase 1-2 细化方案 | `~/.openclaw/workspace/notes/phase1_phase2_detailed_plan.md` |
| main agent 人设 | `~/.openclaw/workspace/SOUL.md` |
| 专家索引 | `~/.openclaw/workspace/memory/expert-registry.md` |
| expert-scout Skill | `~/.openclaw/workspace/skills/expert-scout/SKILL.md` |
| 来源调研报告 | `~/.openclaw/workspace/skills/expert-scout/references/source-research.md` |
| 本地提示词库 | `~/.openclaw/workspace/prompt-library/system-prompt-library/` |
| 数据分析专家 SOUL | `~/.openclaw/workspace-data-analysis-expert/SOUL.md` |

---

## TDD 工作流六阶段概览

```
Phase 0: 苏格拉底式需求澄清 (main agent ↔ 用户)
Phase 1: PRD 生成 (product-manager agent)
Phase 2: 任务拆解 (main agent)
Phase 3: 骨架代码 (dev agent)
Phase 4: 测试编写 — Red (qa-engineer agent)
Phase 5: 代码实现 — Green (dev agent)
Phase 6: 主 Agent 校验 (main agent)
```

---

## 前置条件分析

### 已具备

| 能力 | 现状 | 对应阶段 |
|------|------|---------|
| 需求澄清 | SOUL.md 有"第一性原理"思维 | Phase 0 |
| PRD 生成 | product-manager agent 已有完整 SOUL.md + prd skill | Phase 1 |
| 任务拆解 | SOUL.md 有"规划模式" | Phase 2 |
| 代码编写 | frontend/backend-engineer 已有完整 SOUL.md | Phase 3/5 |
| 测试编写 | qa-engineer 已有 SOUL.md + test-master skill | Phase 4 |

### 缺失（需要补齐）

| 缺口 | 影响 | 优先级 |
|------|------|--------|
| **代码沙盒** — Agent 能否在安全环境执行代码和测试 | Phase 4/5 无法物理执行测试 | P0 阻塞项 |
| **骨架代码规范** — Dev Agent 不知道"只输出签名不写逻辑" | Phase 3 产出不合格 | P1 |
| **TDD 工作流指令** — Agent 不知道完整流程和角色分工 | 全流程 | P1 |
| **任务类型路由** — main 不知道何时走 TDD 流程、何时直接委派 | Phase 0 决策 | P1 |
| **接口变更协议** — 骨架修改时如何通知 QA 同步 | Phase 3-5 协作 | P2 |

---

## 任务清单（按优先级）

### P0: 前置阻塞项

#### Task 1: 评估 OpenClaw 代码执行能力现状 ✅ 已完成 (2026-03-02)
- 调查 OpenClaw 子 Agent 当前能否通过 bash 工具运行 `pytest`/`npm test`
- 确认是否需要独立的 Docker 沙盒，还是现有 bash 已够用
- 如果需要沙盒，评估方案（Docker / 受限 shell / OpenClaw 原生能力）
- **产出**：`notes/code-execution-evaluation.md`
- **结论**：现有 bash 工具足够，无需 Docker 沙盒

### P1: 流程规范

#### Task 2: 定义骨架代码规范 ✅ 已完成 (2026-03-02)
- 创建 `workspace/skills/skeleton-code/SKILL.md`
- 明确骨架文件格式要求：
  - Python: ABC + abstractmethod + 类型签名 + docstring
  - TypeScript: interface/type + 函数签名
  - Dart/Flutter: abstract class + 方法签名
- 明确禁止事项：不写业务逻辑、不写实现、不写 mock
- 提供各语言模板示例
- **产出**：`skills/skeleton-code/SKILL.md`

#### Task 3: 增强 Dev Agent SOUL.md — 骨架模式 ✅ 已完成 (2026-03-02)
- 在 `workspace-frontend-engineer/SOUL.md` 和 `workspace-backend-engineer/SOUL.md` 中增加：
  - "骨架模式"工作指引（收到骨架任务时只输出签名）
  - "实现模式"工作指引（收到实现任务时填充逻辑、跑测试变绿）
  - 两种模式的切换条件
- **产出**：更新后的 Dev Agent SOUL.md（前端 + 后端）

#### Task 4: 增强 QA Agent SOUL.md — TDD 模式 ✅ 已完成 (2026-03-02)
- 在 `workspace-qa-engineer/SOUL.md` 中增加：
  - "基于骨架写测试"工作指引
  - 测试必须物理可执行的要求
  - 覆盖范围：正常路径 + 边界条件 + 异常处理
  - 收到接口变更通知时的同步更新流程
- **产出**：更新后的 QA Agent SOUL.md

#### Task 5: 增强 main agent SOUL.md — 任务类型路由 ✅ 已完成 (2026-03-02)
- 在路由决策中区分任务类型：
  - **开发类任务**（写代码、改 bug、新功能）→ 走 TDD 六阶段流程
  - **分析/报告类任务**（数据分析、竞品报告、调研）→ 直接委派专家
  - **简单任务**（闲聊、查询）→ 自己回答
- 增加"苏格拉底式需求澄清"阶段的具体指引
- 增加 Phase 2 任务拆解要求和 Phase 6 校验动作
- **产出**：更新后的 main SOUL.md

#### Task 6: 创建 TDD 工作流总纲 ✅ 已完成 (2026-03-02)
- 创建 `workspace/notes/tdd-workflow-guide.md` 作为各 Agent 的共享参考
- 内容：完整六阶段流程、每阶段输入/输出、角色分工、文件传递路径
- 这个文件通过 memorySearch.extraPaths 可被所有 Agent 检索到
- **产出**：`notes/tdd-workflow-guide.md`

### P2: 协作机制

#### Task 7: 定义接口变更协议 ✅ 已完成 (2026-03-02)
- 骨架代码确定后，如果 Dev 发现需要修改签名：
  1. Dev 提出变更请求（描述原因 + 新签名）
  2. main agent 审批
  3. 通知 QA agent 同步更新测试
  4. 变更记录写入规划文档
- **产出**：已整合进 `notes/tdd-workflow-guide.md` 的"接口变更协议"章节

#### Task 8: 端到端验证 — 用一个小任务跑完 TDD 全流程 ✅ 已完成 (2026-03-02)
- 选一个简单的开发任务（Calculator 计算器类）
- 走完 Phase 0-6 全流程，26 个测试用例全绿
- 发现 3 个卡点并记录改进建议
- **产出**：`shared/tdd-e2e-test/reports/e2e-verification-report.md`

### P3: 可选优化

#### Task 9: 集成 Agent（可选）
- 当项目规模较大、多模块需要拼装时，引入独立的集成 Agent
- 可通过 expert-scout 从开源社区搜索"CI/CD 专家"或"集成测试专家"
- **产出**：按需引入

---

## 任务依赖关系

```
Task 1 (代码执行评估)
  ↓
  ├── Task 2 (骨架规范)
  ├── Task 3 (Dev Agent 增强)  ← 依赖 Task 2
  ├── Task 4 (QA Agent 增强)   ← 依赖 Task 2
  ├── Task 5 (main 路由增强)
  └── Task 6 (TDD 总纲)       ← 依赖 Task 2-5
        ↓
        Task 7 (变更协议)
        ↓
        Task 8 (端到端验证)    ← 依赖 Task 1-7 全部
```

---

## 关键设计决策记录

1. **选择骨架驱动而非 BDD** — 自然语言不能物理执行，翻译层增加出错率
2. **物理测试优先** — 拒绝口头确认的"虚拟测试"
3. **接口变更可协商** — 原文"不可篡改"过于僵化，改为"变更需通知 QA 同步"
4. **任务类型路由** — TDD 流程只用于开发类任务，分析/报告类直接委派

---

*基于 2026-03-02 与 Gemini 的苏格拉底式讨论 + Claude Code 的落地评估整理*
