# 多智能体架构设计文档

> 基于 2026-03-04 讨论提炼，指导 OpenClaw 多智能体协同架构演进

**创建时间：** 2026-03-04  
**讨论参与：** 刘伟、18 号  
**状态：** 设计中（待实施）

---

## 一、架构模式对比

### 1.1 独立机器人模式（16 个飞书应用）

**核心特征：**
- 每个 AI 员工是独立飞书机器人，有自己的身份、头像、触发器
- 群聊中机器人可以互相@对话
- 完全隔离，互不影响

| 优势 | 劣势 |
|------|------|
| ✅ 身份清晰，用户感知好 | ❌ 运维地狱（16 套配置） |
| ✅ 触发器独立，互不干扰 | ❌ 重复建设（每个都要写心跳） |
| ✅ 权限隔离，故障影响小 | ❌ 协同困难（跨应用通信） |
| ✅ 模型可独立配置 | ❌ 成本不可控（无法全局优化） |
| | ❌ **Token 杀手**（16 份上下文） |

**结论：** 群聊机器人互聊看着热闹，但 token 开销太大，不适合当前场景。

---

### 1.2 中心化调度模式（当前方案）

**核心特征：**
- 1 个主机器人（18 号）+ N 个 sub-agent
- sub-agent 是临时任务，完成后会话归档
- 所有触发器走同一个心跳

| 优势 | 劣势 |
|------|------|
| ✅ 集中运维，配置简单 | ❌ 单点故障风险 |
| ✅ 协同容易，直接调用 | ❌ 身份模糊（都是 18 号） |
| ✅ 成本可控，全局优化 | ❌ 触发器耦合 |
| ✅ 记忆共享（MEMORY.md） | ❌ **sub-agent 无连续对话** |

**结论：** 整体架构合理，但需要改进会话管理和任务追踪机制。

---

### 1.3 混合架构（推荐）

```
1 个主机器人（18 号） + N 个独立专家机器人（高频场景） + sub-agent（低频协同）

主机器人职责：
- 处理日常对话、路由决策
- 维护全局记忆、心跳、日志
- 协调跨专家协同任务

独立机器人（只给高频、独立场景）：
- 财务助手：每天固定报表，独立触发器
- 技术顾问：独立监控、独立告警
- 数学老师：已在独立 workspace，保持现状

sub-agent（需要协同的场景）：
- 前端开发、后端开发、测试验证
- 按项目保持会话（见下文）
```

---

## 二、Sub-agent 会话管理改进

### 2.1 当前问题

**现状：每次 spawn 都是新会话**
```
Phase 3: 骨架代码 → spawn @frontend-engineer (新会话)
  → 完成任务 → 返回结果 → 会话归档

Phase 5: 代码实现 → spawn @frontend-engineer (又一个新会话)
  → 完全不记得 Phase 3 干过什么
  → 重新读取 MEMORY.md + 任务描述 → 重新开工
```

**代价：**
- ❌ 每次重新加载上下文（token 浪费）
- ❌ 没有"这个项目我做过"的连续感
- ❌ 失败重试时不知道之前改了什么

### 2.2 改进方案：任务级上下文传递

**不改会话管理，改任务进度追踪：**

```json
// memory/task-progress.json
{
  "ai-upgrade-frontend": {
    "lastAttempt": {
      "agent": "frontend-engineer",
      "task": "写登录页面",
      "result": "完成，但有 bug",
      "files": ["src/pages/Login.tsx"],
      "issues": ["表单验证没做", "错误提示缺失"],
      "timestamp": "2026-03-04T20:00:00+08:00"
    }
  }
}
```

**派活时：**
```
主 agent → spawn @frontend-engineer
  任务描述：
  "改登录页面的 bug（见上次记录）
   上次尝试：写了 Login.tsx，但没做表单验证和错误提示
   文件位置：src/pages/Login.tsx
   这次重点：补上验证和提示"
```

**优势：**
- ✅ 不需要维护长期会话
- ✅ 上下文通过任务记录传递
- ✅ 主 agent 负责整理进度，sub-agent 只管执行
- ✅ 实现简单（加个任务进度文件）

---

## 三、TDD 流程优化（含任务拆解）

### 3.1 当前流程（SOUL.md 规定）

```
Phase 0: 需求澄清 → 主 agent
Phase 1: PRD 生成 → @product-manager
Phase 2: 任务拆解 → 主 agent（规划模式）
Phase 3: 骨架代码 → @frontend-engineer
Phase 4: 测试编写 → @qa-engineer
Phase 5: 代码实现 → @frontend-engineer
Phase 6: 校验 → 主 agent
```

**缺失环节：**
- ❌ 任务拆解清单没有文件格式规范
- ❌ 子任务状态没人维护
- ❌ 失败重试时没有上下文传递

### 3.2 优化后流程

```
Phase 0: 需求澄清 → 主 agent
Phase 1: PRD 生成 + 任务拆解 → @product-manager
  输出：PRD 文档 + 任务拆解清单（含子任务列表、状态、依赖）
  
Phase 2-N: 执行阶段 → 主 agent 按清单派活
  - 开发 agent 完成任务 → 更新任务状态
  - 主 agent 校验 → 标记完成
  - 失败 → 带上下文重试
```

### 3.3 任务清单文件格式

```markdown
# AI 升级汇报 - 任务拆解清单

**项目：** ai-upgrade-report
**PRD 链接：** `memory/projects/ai-upgrade-prd.md`
**创建时间：** 2026-03-04
**负责人：** @product-manager

## 子任务列表

| ID | 任务描述 | 负责人 | 状态 | 输出文件 | 依赖 | 备注 |
|----|---------|--------|------|---------|------|------|
| T001 | 生成架构图 Mermaid 源码 | @frontend-engineer | ✅ Done | `notes/architecture.mmd` | - | - |
| T002 | 将 Mermaid 转为 SVG | @frontend-engineer | ✅ Done | `notes/architecture.svg` | T001 | - |
| T003 | 编写问答问题清单 | @product-manager | ✅ Done | `notes/demo-qa-questions.md` | - | 8 个问题 |
| T004 | 完成 5 张关键截图 | @user | 🔄 In Progress | `~/Desktop/AI/screenshots/` | T003 | 用户手动执行 |
| T005 | 整理最终材料到桌面 | @ops-agent | ⏳ Pending | `~/Desktop/AI/` | T001,T002,T004 | - |

## 状态说明
- ⏳ Pending：未开始
- 🔄 In Progress：进行中
- ✅ Done：已完成（主 agent 已验证）
- ❌ Failed：失败（需重试）
- 🚫 Blocked：被阻塞（等待依赖）
```

### 3.4 重试逻辑

```
如果任务失败：
1. 在任务清单标记 ❌ Failed
2. 读取上次尝试记录（文件内容、错误信息）
3. 重新 spawn 同一个 agent
4. 任务描述：
   "重试任务 T001：生成架构图 Mermaid 源码
    上次尝试：生成了文件，但格式错误（见下方）
    错误信息：XXX
    文件位置：notes/architecture.mmd
    请修复后重新提交"
```

---

## 四、工作空间与文件共享

### 4.1 当前配置

| Agent | Workspace | 能读主 workspace 吗？ |
|-------|-----------|---------------------|
| main | `/Users/tingjing/.openclaw/workspace` | ✅ |
| product-manager | `/Users/tingjing/.openclaw/workspace-product-manager` | ✅ (extraPaths) |
| frontend-engineer | `/Users/tingjing/.openclaw/workspace-frontend-engineer` | ✅ (extraPaths) |
| backend-engineer | `/Users/tingjing/.openclaw/workspace-backend-engineer` | ✅ (extraPaths) |
| ops-agent | `/Users/tingjing/.openclaw/workspace-ops-agent` | ✅ (extraPaths) |
| qa-engineer | `/Users/tingjing/.openclaw/workspace-qa-engineer` | ❌ **需修复** |
| gpt5-tester | `/Users/tingjing/.openclaw/workspace-gpt5-tester` | ✅ (extraPaths) |
| data-analysis-expert | `/Users/tingjing/.openclaw/workspace-data-analysis-expert` | ✅ (extraPaths) |

### 4.2 文件存放规范

**PRD 和任务清单：** `memory/projects/` 目录
```
/Users/tingjing/.openclaw/workspace/memory/projects/
├── ai-upgrade-prd.md          # PRD 文档
├── ai-upgrade-tasks.md        # 任务拆解清单
└── ai-upgrade-progress.md     # 进度追踪（可选）
```

**原因：**
- ✅ 所有 agent 的 `extraPaths` 已配置可访问
- ✅ 符合"项目信息集中管理"原则
- ✅ 不用改配置，现在就能用

**项目产出文件：** `notes/` 目录
```
/Users/tingjing/.openclaw/workspace/notes/
├── architecture.mmd
├── architecture.svg
├── demo-qa-questions.md
└── screenshot-checklist.md
```

### 4.3 待修复配置

**qa-engineer 需要加 extraPaths：**
```json
{
  "id": "qa-engineer",
  "name": "QA 测试工程师",
  "workspace": "/Users/tingjing/.openclaw/workspace-qa-engineer",
  "model": "bailian/glm-5",
  "memorySearch": {
    "extraPaths": [
      "/Users/tingjing/.openclaw/workspace/MEMORY.md",
      "/Users/tingjing/.openclaw/workspace/memory"
    ]
  }
}
```

---

## 五、实施清单

### 5.1 立刻可做（不改动代码）

- [ ] 创建 `memory/projects/` 目录
- [ ] 为 AI 升级项目写第一个任务清单（试点）
- [ ] 改 SOUL.md 规定 PRD 和任务清单存放位置

### 5.2 需要改配置

- [ ] 给 `qa-engineer` 加 `extraPaths`（改 `openclaw.json`）
- [ ] 改 SOUL.md 的 TDD 流程（Phase 1 包含任务拆解）
- [ ] 改 SOUL.md 的派活逻辑（带任务进度上下文）

### 5.3 后续优化（汇报后）

- [ ] 心跳检查增加任务清单状态检查
- [ ] 任务进度文件模板标准化
- [ ] 独立机器人原型（财务助手试点）

---

## 六、核心原则

1. **文件可靠，记忆不持久** —— 所有进度写文件，不靠脑子记
2. **主 agent 是调度员，不是执行者** —— 能分配的都分配，主 agent 负责追踪进度
3. **重试必须带上下文** —— 失败重试时告诉 agent 上次做了什么、错在哪里
4. **任务状态由执行者更新** —— 开发 agent 完成后自己改状态，不是主 agent 追着问
5. **token 节省优先** —— 不盲目搞独立机器人，会话保持要谨慎

---

*此文档持续更新，每次架构决策后补充经验教训。*
