# TDD 工作流指南 — 骨架驱动开发

> OpenClaw 多智能体体系的标准开发流程
> 适用于：所有开发类任务（新功能、重构、bug 修复中的结构性改动）

---

## 流程总览

```
用户需求
  ↓
Phase 0: 苏格拉底式需求澄清   [main agent ↔ 用户]
  ↓
Phase 1: PRD 生成              [product-manager]  (sessions_spawn)
  ↓
Phase 2: 任务拆解              [main agent]
  ↓
Phase 3: 骨架代码              [dev agent — 骨架模式]  (sessions_send)
  ↓
Phase 4: 测试编写 (Red)        [qa-engineer — TDD 模式]  (sessions_send)
  ↓
Phase 5: 代码实现 (Green)      [dev agent — 实现模式]  (sessions_send 延续 Phase 3)
  ↓
Phase 6: 主 Agent 校验         [main agent]
  ↓
交付用户
```

---

## 通讯策略

| 场景 | 方式 | 理由 |
|------|------|------|
| Phase 1 PRD 生成 | `sessions_spawn` | 一次性任务，不需要上下文延续 |
| Phase 3 骨架代码 | `sessions_send` | 建立持久 session，Phase 5 需要延续 |
| Phase 4 测试编写 | `sessions_send` | 建立持久 session，接口变更时需要延续 |
| Phase 5 代码实现 | `sessions_send` | 延续 Phase 3 的 session，agent 记得自己写的骨架 |
| Phase 5 失败重试 | `sessions_send` | 延续同一 session，带着失败上下文继续 |
| 接口变更通知 QA | `sessions_send` | 延续 Phase 4 的 session，QA 记得测试结构 |

**Session Key 约定：**
- Dev Agent: `agent:{dev-agent-id}:tdd:{project-name}`
- QA Agent: `agent:qa-engineer:tdd:{project-name}`
- 项目结束后 session 自然过期（idle 120min 自动 reset）

---

## 任务文件规范（task-breakdown.md）

### 文件路径

每个项目的任务文件统一放在：`workspace/shared/{project-name}/task-breakdown.md`

### 格式模板

```markdown
# 任务拆解 — {项目名称}

## 元信息
- PRD: {PRD 文件绝对路径}
- 创建时间: YYYY-MM-DD
- 项目状态: pending | in_progress | completed | blocked

## 子任务

### T1: {子任务名称}
- 负责人: {agent-id}
- 状态: pending | in_progress | completed | failed
- 依赖: (无) 或 T2
- Phase 3:
  - 骨架文件: (待填)
  - Stub 文件: (待填)
- Phase 4:
  - 测试文件: (待填)
  - 用例数: (待填)
  - Red 确认: (待填)
- Phase 5:
  - 实现文件: (待填)
  - 测试结果: (待填)
- 失败记录: (无)

### T2: {子任务名称}
- ...（同上格式）

## 接口变更记录
（按需追加）
```

### 状态流转规则

```
pending → in_progress → completed
                ↘ failed → in_progress（重试）
```

- **pending**: main agent 创建任务时的初始状态
- **in_progress**: dev/qa agent 开始工作时自己改
- **completed**: dev/qa agent 完成并验证通过后自己改，同时填写产出文件路径
- **failed**: dev/qa agent 失败时自己改，同时追加失败记录

### 谁改什么

| 角色 | 可修改的字段 |
|------|------------|
| main agent | 创建整个文件、项目状态、审批接口变更 |
| dev agent | 自己负责的子任务的：状态、Phase 3/5 产出路径、失败记录 |
| qa agent | 自己负责的子任务的：Phase 4 产出路径、用例数、Red 确认 |

---

## 各阶段详解

### Phase 0: 苏格拉底式需求澄清

| 项目 | 说明 |
|------|------|
| **执行者** | main agent |
| **输入** | 用户的原始需求描述 |
| **输出** | 结构化需求摘要（交给 product-manager） |
| **方法** | 每轮 2-3 个关键问题；用"如果……会怎样？"引导思考边界 |
| **退出条件** | 目标用户、核心问题、成功标准三项明确 |

### Phase 1: PRD 生成

| 项目 | 说明 |
|------|------|
| **执行者** | `@product-manager`（`sessions_spawn`） |
| **输入** | Phase 0 的结构化需求摘要 |
| **输出** | PRD 文档（写入 `workspace/shared/{project}/prd/`） |
| **使用 Skill** | `prd` |
| **交付物** | PRD 文件绝对路径 |

### Phase 2: 任务拆解

| 项目 | 说明 |
|------|------|
| **执行者** | main agent（规划模式） |
| **输入** | PRD 文档 |
| **输出** | `task-breakdown.md`，按上方格式模板填写 |
| **粒度** | 1 个骨架文件 = 1 个子任务 |
| **要求** | 每个子任务必须有：负责人、依赖关系、验收标准 |

### Phase 3: 骨架代码

| 项目 | 说明 |
|------|------|
| **执行者** | `@frontend-engineer` 或 `@backend-engineer`（骨架模式） |
| **通讯** | `sessions_send`（建立持久 session） |
| **派发指令** | "请执行 {task-breakdown.md 绝对路径} 中的 {T1}，Phase 3 骨架模式。" |
| **输入** | 任务文件路径 + 子任务 ID + PRD 路径 |
| **输出** | 骨架文件 + stub 文件 |
| **使用 Skill** | `skeleton-code` |
| **完成动作** | agent 自行更新 task-breakdown.md：状态→completed，填写产出路径 |
| **失败动作** | agent 自行更新 task-breakdown.md：状态→failed，追加失败记录 |

### Phase 4: 测试编写 (Red)

| 项目 | 说明 |
|------|------|
| **执行者** | `@qa-engineer`（TDD 模式） |
| **通讯** | `sessions_send`（建立持久 session） |
| **派发指令** | "请执行 {task-breakdown.md 绝对路径} 中的 {T1}，Phase 4 测试编写。骨架/stub 路径见任务文件。" |
| **输入** | 任务文件路径 + 子任务 ID |
| **输出** | 测试文件（从 stub 文件 import 被测类，此时全 FAIL 是正确的） |
| **使用 Skill** | `test-master` |
| **覆盖范围** | 正常路径 + 边界条件 + 异常处理 |
| **验证** | 测试可运行（Python: `python3.12 -m pytest` / TS: `npx vitest run` / Dart: `flutter test`），全部 Red |
| **完成动作** | agent 自行更新 task-breakdown.md：填写测试文件路径、用例数、Red 确认 |

### Phase 5: 代码实现 (Green)

| 项目 | 说明 |
|------|------|
| **执行者** | `@frontend-engineer` 或 `@backend-engineer`（实现模式） |
| **通讯** | `sessions_send`（延续 Phase 3 的 session） |
| **派发指令** | "继续 {T1}，Phase 5 实现模式。测试文件路径见 task-breakdown.md。" |
| **输入** | 任务文件路径 + 子任务 ID（agent 已有 Phase 3 的上下文） |
| **输出** | 实现代码（填充 stub，所有测试变绿） |
| **约束** | 不得修改函数签名（需改时走接口变更协议） |
| **验证** | 运行测试，全部 Green |
| **完成动作** | agent 自行更新 task-breakdown.md：状态→completed，填写实现路径 + 测试结果 |
| **失败动作** | agent 自行更新 task-breakdown.md：状态→failed，追加失败记录 |

**失败重试：** main agent 通过 `sessions_send` 发送到同一 session："T1 Phase 5 上次失败，原因见 task-breakdown.md 的失败记录，请继续修复。"

### Phase 6: 主 Agent 校验

| 项目 | 说明 |
|------|------|
| **执行者** | main agent |
| **输入** | task-breakdown.md（检查所有子任务状态） |
| **动作** | 读取任务文件，确认所有子任务 completed；如有 failed，触发重试 |
| **退出条件** | 所有子任务 completed + 测试全绿 |
| **输出** | 更新项目状态为 completed，向用户汇报最终结果 |

---

## 文件传递路径

```
workspace/shared/{project-name}/
├── prd/
│   └── {project}-prd.md        ← Phase 1 产出
├── task-breakdown.md            ← Phase 2 产出（全流程共用的状态中心）
├── domain/                      ← Phase 3 骨架代码
│   ├── user_repository.py
│   └── user_service.py
├── infra/                       ← Phase 3 stub + Phase 5 实现
│   ├── user_repository_impl.py
│   └── user_service_impl.py
├── tests/                       ← Phase 4 测试代码
│   ├── test_user_repository.py
│   └── test_user_service.py
└── reports/                     ← 校验报告
    └── verification-report.md
```

---

## 接口变更协议

骨架代码（Phase 3）确定后，签名即为契约。如 Dev Agent 在 Phase 5 发现需要修改：

1. **Dev Agent 提出变更请求** — 在 task-breakdown.md 的"接口变更记录"追加请求，状态设为"待审批"
2. **main agent 审批** — 评估影响范围，决定是否批准，状态改为"已批准"
3. **通知 QA Agent 同步** — 通过 `sessions_send` 延续 QA 的 session，通知更新测试
4. **QA Agent 确认同步** — 更新测试 + 重新验证 Red 状态，状态改为"已同步"
5. **Dev Agent 继续实现** — 使用新签名完成实现

**变更记录格式（写入 task-breakdown.md）：**
```
## 接口变更记录
- [日期] `UserRepository.find_by_id` 返回值从 `User | None` 改为 `Result[User]`
  - 原因：需要区分"不存在"和"查询失败"
  - 影响任务：T1
  - 影响测试：test_find_by_id_* (3 个)
  - 状态：待审批 | 已批准 | 已同步
```

---

## 何时走 TDD 流程 vs 直接委派

| 场景 | 走 TDD 六阶段 | 直接委派 |
|------|:---:|:---:|
| 新功能开发 | ✅ | |
| 结构性重构 | ✅ | |
| 复杂 bug 修复（需改接口） | ✅ | |
| 简单 bug 修复（改几行） | | ✅ |
| 数据分析/报告 | | ✅ |
| 文档编写 | | ✅ |
| UI 微调（颜色/间距） | | ✅ |

**判断原则：** 如果任务涉及新建或修改接口/类/模块 → 走 TDD。如果是局部修改且不影响接口 → 直接委派。

---

## 关键设计决策

1. **骨架驱动而非 BDD** — 代码签名可编译执行，自然语言不能
2. **物理测试优先** — 测试必须用 pytest/npm test/flutter test 实际运行，拒绝口头确认
3. **接口变更可协商** — 不是"不可篡改"，而是"变更需审批 + 通知 QA 同步"
4. **代码执行直接用 bash** — 无需 Docker 沙盒，本机环境已具备所有测试运行器
5. **持久对话延续上下文** — Phase 3→5 用 `sessions_send` 保持 dev agent session，省 token + 减少出错
6. **任务文件是唯一真相源** — `task-breakdown.md` 是所有 agent 共享的状态中心，agent 自行更新自己负责的字段
7. **文件化派发** — 派发时引用任务文件路径 + 子任务 ID，不把整个需求塞进 spawn 参数

---

*本文件可通过 memorySearch.extraPaths 被所有 Agent 检索。*
*基于 2026-03-02 架构规划，2026-03-04 更新通讯策略和任务状态管理。*
