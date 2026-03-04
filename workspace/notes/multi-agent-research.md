# Multi-Agent 协作方案调研报告

> 调研日期：2026-03-02  
> 目标：调研成熟的多智能体协作方案，为优化 OpenClaw 多智能体能力提供参考

---

## 一、主流 Multi-Agent 框架概述

### 1. CrewAI

**定位**：角色驱动的多智能体编排框架，强调快速原型开发和角色分工。

**核心概念**：
- **Agent**：具有角色、目标、工具集的自主行动者
- **Crew**：协作团队，配置为达成高级目标
- **Flow**：结构化的工作流，管理状态和执行控制

**通信机制**：
- 基于 CrewWorkflow 定义顺序、并行或层级工作流
- 协作式消息传递（collaborative crews）
- Manager-agent 模式：管理型 Agent 控制子 Agent

**优势**：
- 简单易用，快速上手
- 角色定义清晰
- 支持多种工作流模式（顺序、并行、层级）
- 与 LangChain/LangGraph 生态集成良好

**劣势**：
- 确定性较低，Agent 可能陷入无限循环
- 生产环境可靠性有限
- 工作流结构化程度不如 LangGraph

---

### 2. Microsoft AutoGen

**定位**：对话式多智能体框架，强调 Agent 间的消息传递和对话协作。

**核心概念**：
- **ConversableAgent**：可对话的 Agent 基类
- **AssistantAgent**：AI 助手角色
- **UserProxyAgent**：用户代理，管理任务分发

**通信机制**：
- 自动回复机制（auto-reply）：Agent 自主响应消息
- 消息传递编排：通过 `register_reply()` 注册回复函数
- 对话链模式：Agent 间通过对话协作完成任务

**任务分发模式**：
- UserProxyAgent 作为"项目经理"，接收请求并分解任务
- 委托给专业 AssistantAgent 执行
- 收集输出并传递给下一个 Agent

**优势**：
- 对话式协作直观易懂
- 支持人类介入（human-in-the-loop）
- 灵活的消息传递机制

**劣势**：
- 执行流程控制较难
- 缺乏生产级编排工具
- 可能出现无限循环或 Agent 冲突

**演进**：Microsoft 已推出 Agent Framework，融合 AutoGen 和 Semantic Kernel，增加工作流编排能力。

---

### 3. LangGraph (LangChain)

**定位**：图驱动的 Agent 工作流引擎，强调状态管理和确定性控制。

**核心概念**：
- **StateGraph**：状态图，定义工作流节点和边
- **Node**：Agent 或处理单元
- **Edge**：节点间的转移，支持条件路由

**通信机制**：
- 共享状态（State）：Agent 通过读写共享状态通信
- 条件边：基于状态值决定下一个执行路径
- 子图（Subgraph）：模块化的 Agent 组

**任务分发模式**：
- **Scatter-gather**：任务分发到多个 Agent，结果汇总
- **Pipeline**：顺序流水线处理
- **Parallel execution**：并行执行后合并

**优势**：
- 确定性高，可预测执行路径
- 支持循环和条件分支
- 内置持久化和调试能力
- 生产级可靠性

**劣势**：
- 学习曲线较陡
- 复杂工作流需要大量代码
- 过度工程化风险

---

### 4. MetaGPT

**定位**：模拟软件公司的多智能体框架，以 SOP（标准作业流程）为核心。

**核心概念**：
- **SOP**：标准化作业流程，定义 Agent 协作规范
- **角色专业化**：产品经理、架构师、项目经理、工程师、QA

**通信机制**：
- 发布-订阅机制：Agent 通过共享 workspace 交换消息
- 结构化输出：PRD、设计文档、代码等标准化产物

**任务分发模式**：
```
用户需求 → 产品经理(PRD) → 架构师(设计) → 项目经理(任务分解) → 工程师(编码) → QA(测试)
```

**优势**：
- SOP 驱动，协作规范明确
- 模拟真实软件开发流程
- 代码生成质量高（MBPP 提升 5.4%）

**劣势**：
- 偏向软件开发生成场景
- 角色固化，灵活性有限
- 学习成本较高

---

### 5. CAMEL AI

**定位**：可扩展的通讯式智能体框架，强调自主协作和大规模模拟。

**核心概念**：
- **Role-playing**：角色扮演机制，通过 inception prompting 引导对话
- **Workforce**：大规模 Agent 管理
- **Stateful Memory**：有状态记忆

**通信机制**：
- 自主通信：Agent 独立交互，减少人类干预
- 动态通信：实时 Agent 间交互
- 支持百万级 Agent 模拟

**优势**：
- 高可扩展性（支持百万 Agent）
- 自主性强，减少人类干预
- 适合研究和实验

**劣势**：
- 生产环境稳定性待验证
- 调试复杂度高
- 主要是研究导向

---

### 6. AgentVerse

**定位**：多智能体协作平台，模拟人类群体问题解决过程。

**核心概念**：
- **Differentiation Plane**：专业化资产（知识库、工具）
- **Intelligence Plane**：Agent 基础设施
- **Experience Plane**：用户界面层

**通信机制**：
- 标准化消息格式
- 多 Agent 协作协议
- 并行工作流

**优势**：
- 端到端平台
- 支持 Minecraft 等复杂环境
- ICLR 2024 论文验证

**劣势**：
- 无可视化构建器
- 无托管方案
- 社区活跃度一般

---

## 二、调研维度对比表

| 维度 | CrewAI | AutoGen | LangGraph | MetaGPT | CAMEL | AgentVerse |
|------|--------|---------|-----------|---------|-------|------------|
| **通信机制** | 消息传递 | 对话式 | 共享状态 | 发布订阅 | 自主通信 | 标准消息 |
| **任务分发** | Crew/Flow | UserProxy | StateGraph | SOP 流程 | Role-playing | 并行工作流 |
| **角色定义** | 自定义角色 | Assistant/Proxy | 节点配置 | 5 种固定角色 | 自定义角色 | 自定义 |
| **上下文共享** | Crew 级别 | 对话历史 | State | Workspace | Memory | 消息格式 |
| **冲突处理** | 有限 | 有限 | 条件路由 | SOP 约束 | 协商机制 | 协议约束 |
| **结果汇总** | Flow 聚合 | 收集输出 | State 合并 | 顺序产出 | 自主汇总 | 并行汇总 |
| **生产成熟度** | 中 | 中 | 高 | 中 | 低 | 低 |

---

## 三、通信与协调模式深度分析

### 3.1 四种核心委托架构

根据业界最佳实践，多智能体系统主要采用以下四种模式：

#### 1. Sequential Handoff（顺序传递）
```
Agent A → Agent B → Agent C → 输出
```
- 适用：线性流水线任务
- 优势：简单可控
- 风险：串行瓶颈

#### 2. Coordinator-Dispatcher（协调者调度）
```
          ┌→ Specialist A
User → Coordinator → Specialist B
          └→ Specialist C
```
- 适用：多领域任务路由
- 优势：灵活分发
- 风险：协调者成为瓶颈

#### 3. Orchestrator-Worker（编排者-工作者）
```
Orchestrator → 分解任务 → Workers 执行 → 结果聚合
```
- 适用：复杂任务并行处理
- 优势：并行效率高
- 风险：结果合并复杂

#### 4. Agents-as-Tools（工具化代理）
```
Main Agent → 调用 Specialist Agent（作为工具）
```
- 适用：专业领域明确
- 优势：简单直接
- 风险：层级单一

### 3.2 通信协议对比

| 协议类型 | 代表框架 | 优势 | 劣势 |
|----------|----------|------|------|
| 消息传递 | AutoGen, CrewAI | 灵活、可扩展 | 易失控 |
| 共享状态 | LangGraph | 确定性高 | 状态管理复杂 |
| 发布订阅 | MetaGPT | 解耦良好 | 时序问题 |
| 工具调用 | OpenAI Swarm, OpenClaw | 简单直接 | 层级限制 |

---

## 四、OpenClaw 现状分析

### 4.1 当前机制

OpenClaw 提供两个核心 API：

| API | 功能 | 类比 |
|-----|------|------|
| `sessions_spawn` | 派分身执行独立任务 | "派实习生去干活" |
| `sessions_send` | 向现有 Agent 发消息 | "打内线电话" |

### 4.2 现有模式

根据 OpenClaw 文档和社区实践，主要模式包括：

#### Coordinator-Specialist 模式
```
Coordinator Agent
    ├── sessions_spawn → Research Specialist
    ├── sessions_spawn → Dev Specialist  
    └── sessions_spawn → QA Specialist
```

**特点**：
- Coordinator 持有 MEMORY.md，负责持久化
- Specialist 无状态，执行后返回结果并终止
- 通过工具权限控制防止循环

#### 文件主控模式
```
所有 Agent → sessions_send → File Master → SSH/NAS
```
- 集中管理文件操作
- 单一入口，防止冲突

### 4.3 当前局限

| 局限 | 描述 |
|------|------|
| 无共享状态 | 每个 spawn 的 Agent 上下文隔离 |
| 无动态任务认领 | Agent 只能执行 spawn 时分配的任务 |
| 无依赖追踪 | 无法表达 Agent 间的依赖关系 |
| 手动路由 | 需要显式调用 sessions_send |

---

## 五、框架对比与借鉴建议

### 5.1 OpenClaw vs 其他框架

| 维度 | OpenClaw | CrewAI | LangGraph | AutoGen |
|------|----------|--------|-----------|---------|
| **模型** | 会话级隔离 | Crew 共享 | State 共享 | 对话共享 |
| **路由** | 手动 sessions_send | 自动工作流 | 条件边 | 对话链 |
| **状态** | Agent 级 MEMORY.md | Crew 级 | StateGraph | 对话历史 |
| **工具权限** | 细粒度控制 | 全局 | 全局 | 全局 |
| **生产度** | 高 | 中 | 高 | 中 |

### 5.2 可借鉴的设计模式

#### 从 LangGraph 借鉴：
1. **条件路由**：基于 Agent 输出决定下一步
2. **状态管理**：引入共享 Task State
3. **子图模式**：Agent 组作为可复用单元

#### 从 MetaGPT 借鉴：
1. **SOP 规范**：标准化协作流程
2. **角色专业化**：明确 Agent 能力边界
3. **结构化输出**：定义 Agent 间的接口契约

#### 从 CrewAI 借鉴：
1. **Flow 抽象**：工作流与 Agent 解耦
2. **重试机制**：内置失败处理
3. **人类反馈**：human-in-the-loop 支持

#### 从 AutoGen 借鉴：
1. **对话式协作**：Agent 间自然语言交互
2. **回复注册机制**：可扩展的消息处理

---

## 六、针对 minimax-expert-importer 的优化建议

### 6.1 当前问题

根据 SKILL.md 分析，当前 minimax-expert-importer 是单 Agent 工作流：
- 一个 Agent 完成所有步骤（浏览、搜索、抓取、创建）
- 无并行能力
- 无角色分工

### 6.2 多 Agent 重构方案

#### 方案一：Coordinator-Specialist 架构

```
┌─────────────────────────────────────────────────┐
│              Expert Import Coordinator           │
│  (主控 Agent，负责用户交互、任务分配、结果汇总)    │
└─────────────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Web Browser  │ │ Prompt Parser│ │ Skill Creator│
│   Specialist │ │   Specialist │ │   Specialist │
└──────────────┘ └──────────────┘ └──────────────┘
```

**角色定义**：

| Agent | 职责 | 工具权限 |
|-------|------|----------|
| Coordinator | 接收请求、分类、分发、汇总 | sessions_spawn, sessions_send, read, write |
| Web Browser Specialist | 浏览 MiniMax 平台，抓取专家信息 | browser, read |
| Prompt Parser Specialist | 解析提示词，提取关键信息 | read, write |
| Skill Creator Specialist | 创建 SKILL.md，组织目录结构 | read, write, edit |

**通信协议**：
```yaml
# Coordinator → Web Browser Specialist
sessions_spawn({
  task: "访问 MiniMax 专家平台，抓取 UI/UX 类别的前 5 个专家信息",
  runtime: "subagent"
})

# Coordinator → Prompt Parser Specialist  
sessions_send({
  sessionKey: "agent:parser:main",
  message: "解析以下专家提示词：[内容]"
})

# Coordinator → Skill Creator Specialist
sessions_send({
  sessionKey: "agent:creator:main",
  message: "创建技能：[解析后的结构化数据]"
})
```

#### 方案二：流水线模式（Sequential Handoff）

```
User Request → Browser Agent → Parser Agent → Creator Agent → Output
```

**适用场景**：单次导入任务，流程固定

**实现**：
```javascript
// Step 1: Browser Agent 抓取
const rawData = await sessions_spawn({
  task: "抓取 MiniMax 专家信息",
  label: "browser-agent"
})

// Step 2: Parser Agent 解析
const parsedData = await sessions_spawn({
  task: `解析专家数据：${rawData}`,
  label: "parser-agent"
})

// Step 3: Creator Agent 创建
const result = await sessions_spawn({
  task: `创建技能：${parsedData}`,
  label: "creator-agent"
})
```

#### 方案三：并行批量导入

```
                    ┌→ Browser Agent 1 → Parser → Creator → Skill 1
                    │
User Request →      ├→ Browser Agent 2 → Parser → Creator → Skill 2
                    │
                    └→ Browser Agent 3 → Parser → Creator → Skill 3
```

**适用场景**：批量导入多个专家

**实现**：
```javascript
// 并行 spawn 多个独立导入流程
const experts = ["ui-ux-designer", "frontend-dev", "data-analyst"]

const tasks = experts.map(expert => 
  sessions_spawn({
    task: `导入专家：${expert}`,
    label: `import-${expert}`,
    runtime: "subagent"
  })
)

// 等待所有任务完成
const results = await Promise.all(tasks)
```

### 6.3 具体优化建议

#### 1. 引入专家分类索引

```markdown
# references/expert-index.md

## 产品设计类
- ui-ux-designer: UI/UX 设计专家
- prd-assistant: PRD 编写助手
- saas-niche-finder: SaaS 利基市场分析

## 前端开发类
- landing-page-builder: 落地页构建
- pptx-maker: PPT 生成
- principle-animator: 动效设计
```

#### 2. 标准化 Agent 间消息格式

```typescript
interface ExpertImportMessage {
  type: 'fetch' | 'parse' | 'create'
  expertId: string
  category: string
  rawData?: string
  parsedData?: ParsedExpert
  outputPath?: string
}
```

#### 3. 添加失败重试机制

```javascript
// 参考 LangGraph 的重试模式
async function importWithRetry(expertId, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await sessions_spawn({ task: `导入 ${expertId}` })
    } catch (error) {
      if (i === maxRetries - 1) throw error
      await sleep(1000 * (i + 1))
    }
  }
}
```

#### 4. 引入状态追踪

```markdown
# memory/import-state.md

## 进行中的导入
- [ ] ui-ux-designer (2026-03-02 14:00)
- [x] frontend-dev (2026-03-02 13:30)

## 失败的导入
- backend-expert: 浏览器超时，需重试
```

#### 5. 工具权限隔离

```json
{
  "coordinator": {
    "allow": ["sessions_spawn", "sessions_send", "read", "write"],
    "deny": ["browser", "exec"]
  },
  "browser-specialist": {
    "allow": ["browser", "read"],
    "deny": ["sessions_spawn", "sessions_send", "write"]
  },
  "creator-specialist": {
    "allow": ["read", "write", "edit"],
    "deny": ["browser", "sessions_spawn"]
  }
}
```

### 6.4 推荐架构选择

**短期优化**：采用方案一（Coordinator-Specialist），复用现有 sessions_spawn/sessions_send 机制。

**长期目标**：参考 LangGraph 的 StateGraph 模式，引入：
- 任务状态共享
- 条件路由
- 并行执行支持

---

## 七、总结

### 核心发现

1. **通信模式多样化**：各框架采用不同的通信机制（消息传递、共享状态、发布订阅），选择取决于任务复杂度和确定性需求。

2. **SOP 是关键**：MetaGPT 的成功证明，标准化作业流程能显著提升多 Agent 协作质量。

3. **状态管理是核心挑战**：LangGraph 的 State 是最成熟的状态管理方案，值得借鉴。

4. **OpenClaw 的优势**：
   - 细粒度工具权限控制
   - 会话级隔离保证稳定性
   - 已有成熟的 Coordinator-Specialist 模式

5. **OpenClaw 的改进空间**：
   - 缺乏共享任务状态
   - 无条件路由能力
   - 无并行执行原生支持

### 下一步行动

1. **短期**：为 minimax-expert-importer 实现 Coordinator-Specialist 架构
2. **中期**：设计并实现共享任务状态机制
3. **长期**：探索条件路由和并行执行能力

---

## 参考资料

- [CrewAI Documentation](https://docs.crewai.com)
- [Microsoft AutoGen Paper](https://arxiv.org/abs/2308.08155)
- [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph)
- [MetaGPT Paper (ICLR 2024)](https://arxiv.org/abs/2308.00352)
- [CAMEL AI GitHub](https://github.com/camel-ai/camel)
- [AgentVerse Paper (ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024)
- [OpenClaw Multi-Agent Documentation](https://docs.openclaw.ai/concepts/multi-agent)
- [OpenClaw Multi-Agent Coordination Guide](https://lumadock.com/tutorials/openclaw-multi-agent-coordination-governance)