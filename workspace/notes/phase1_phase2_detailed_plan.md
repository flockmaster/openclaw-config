# Phase 1 & Phase 2 细化实现方案

> 核心原则：不靠模型临时生成提示词，而是从开源社区引入经过验证的专家方案；
> 通过 Skill 解耦"专家获取"能力；完全基于 OpenClaw 现有原语，不魔改框架。

---

## 〇、现状分析：OpenClaw 已有什么？

在设计之前先盘清家底，避免重复造轮子：

| 已有能力 | 对应机制 | 位置 |
|---------|---------|------|
| Agent 注册 | `openclaw.json` → `agents.list[]` | 配置文件 |
| Agent 人设 | `SOUL.md` (角色、擅长、原则、调性) | `agents/<id>/agent/` |
| 子 Agent 委派 | `AGENTS.md` + `subagents.allowAgents` | Agent 目录 |
| Skill 热加载 | `SKILL.md` + `skills.load.extraDirs` + `watch:true` | `workspace/skills/` |
| 专家抓取先例 | `minimax-expert-importer` Skill | `workspace/skills/` |
| 飞书路由绑定 | `bindings[]` (agentId ↔ 群/私聊) | `openclaw.json` |
| 已有专家团队 | 8 个 Agent（main/前端/后端/产品/QA/运营/数学/测试） | `agents/` |

**关键发现**：OpenClaw 的 Agent 系统本身就是"专家注册表" + "路由中枢"。
我们不需要另起炉灶，而是在现有体系上增强两件事：
1. **专家的来源** — 从"自己写 SOUL.md"升级为"从开源社区引入验证过的方案"
2. **路由的智能化** — 从"静态绑定"升级为"按需发现 + 动态引入"

---

## 一、Phase 1：专家注册表（改进版）

### 1.1 设计思路

**原方案问题**：在 `openclaw.json` 里新增一个 `experts` 字段，脱离了现有 `agents` 体系，
将来 OpenClaw 升级 agents 相关功能时，`experts` 字段不会被框架识别，改动白费。

**改进方案**：完全复用 OpenClaw 的原生 Agent 体系，但增加一层**元数据规范**来区分
"自建专家"和"引入专家"，以及记录专家来源和质量信息。

### 1.2 专家目录结构（复用原生格式）

```
~/.openclaw/agents/<expert-id>/agent/
├── SOUL.md              # 专家人设（核心提示词）
├── EXPERT-META.md       # 【新增】专家元数据（来源、版本、评分）
├── AGENTS.md            # 可选：该专家可以委派的子专家
├── models.json          # 可选：专家专属模型偏好
└── references/          # 可选：专家参考资料
    ├── original-prompt.md   # 原始提示词存档（便于溯源）
    └── changelog.md         # 本地化改动记录
```

### 1.3 EXPERT-META.md 规范

这是唯一新增的文件，用于记录专家的"血统"信息：

```markdown
# Expert Metadata

## 来源
- **平台**: minimax / github / langchain-hub / custom
- **原始 ID**: ui-ux-designer
- **原始 URL**: https://agent.minimax.io/experts/ui-ux-designer
- **引入时间**: 2026-03-02
- **引入方式**: expert-scout skill

## 质量
- **验证状态**: verified | unverified | adapted
- **适配说明**: 基于 MiniMax 原版，增加了中文输出要求和飞书工具集成
- **使用次数**: 12
- **最近使用**: 2026-03-01

## 兼容性
- **OpenClaw 版本**: 2026.2.24
- **依赖 Skills**: shadcn-ui, tailwindcss
- **推荐模型**: bailian/kimi-k2.5
```

**为什么用 `.md` 而不是 `.json`？**
- 与 OpenClaw 的 `SOUL.md`、`AGENTS.md` 保持一致的约定
- OpenClaw 未来升级不会受影响（框架只识别 `SOUL.md`，额外的 `.md` 文件会被忽略）
- 人类可读，方便手动编辑

### 1.4 注册到 openclaw.json（复用原生方式）

引入的专家和现有 Agent 一样注册，完全走原生流程：

```json
// openclaw.json → agents.list 中新增一条
{
  "id": "ui-ux-expert",
  "name": "UI/UX 设计专家",
  "workspace": "/Users/tingjing/.openclaw/workspace-ui-ux-expert",
  "agentDir": "/Users/tingjing/.openclaw/agents/ui-ux-expert/agent",
  "model": "bailian/kimi-k2.5",
  "memorySearch": {
    "extraPaths": [
      "/Users/tingjing/.openclaw/workspace/MEMORY.md",
      "/Users/tingjing/.openclaw/workspace/memory"
    ]
  }
}
```

**好处**：
- 引入的专家和手动创建的 Agent 在系统里地位完全相同
- 可以被 `@ui-ux-expert` 委派、可以绑定飞书群、可以有独立 workspace
- OpenClaw 的 subagent 并发控制、超时机制、会话管理全部自动生效
- 框架升级时，所有 agent 相关改进自动惠及引入的专家

### 1.5 专家分类索引

在 workspace 中维护一个轻量索引文件，便于 Manager 快速查找：

```
~/.openclaw/workspace/memory/expert-registry.md
```

```markdown
# 已注册专家索引

## 自建专家
| ID | 名称 | 领域 | 模型 | 飞书群绑定 |
|----|------|------|------|-----------|
| frontend-engineer | 前端工程师 | 前端开发 | kimi-k2.5 | oc_34f05... |
| backend-engineer | 后端工程师 | 后端开发 | qwen3.5-plus | oc_34f05... |
| product-manager | 产品经理 | 产品设计 | qwen3.5-plus | oc_2e74c... |

## 引入专家（来自开源社区）
| ID | 名称 | 领域 | 来源 | 验证状态 | 引入时间 |
|----|------|------|------|---------|---------|
| ui-ux-expert | UI/UX 设计专家 | 设计 | minimax | verified | 2026-03-02 |
| clickhouse-expert | ClickHouse 专家 | 数据库 | github | adapted | 2026-03-01 |

## 领域覆盖情况
- [x] 前端开发
- [x] 后端开发
- [x] 产品设计
- [x] 测试 QA
- [ ] 数据分析 ← 缺口，需引入
- [ ] DevOps ← 缺口，需引入
- [ ] 安全审计 ← 缺口，需引入
```

这个索引文件会被 main agent 通过 `memorySearch.extraPaths` 自动加载，
实现"Manager 知道自己有哪些专家可用"。

---

## 二、Phase 2：路由中枢 + 专家发现 Skill

### 2.1 设计思路

路由中枢分为两层：

```
┌─────────────────────────────────────────────┐
│              用户需求进入                      │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  第一层：静态路由（OpenClaw 原生 bindings）    │
│                                              │
│  飞书产品群 → product-manager                 │
│  飞书技术群 → frontend-engineer               │
│  飞书数学群 → math-teacher                    │
│  私聊      → main agent                      │
└─────────────┬───────────────────────────────┘
              │ 当 main agent 收到需求时
              ▼
┌─────────────────────────────────────────────┐
│  第二层：智能路由（main agent 的增强 SOUL.md） │
│                                              │
│  判断流程：                                   │
│  1. 自己能答？→ 直接回答                       │
│  2. 已有专家能答？→ @expert-id 委派            │
│  3. 没有合适专家？→ 触发 expert-scout Skill    │
│     → 搜索开源社区 → 引入新专家 → 再委派       │
└─────────────────────────────────────────────┘
```

### 2.2 增强 main agent 的 SOUL.md

在现有 SOUL.md 基础上增加路由决策指引：

```markdown
# main agent - 主代理

## 语言要求
**必须使用中文输出**

## 你的角色
主协调代理，负责理解用户意图、分配任务、协调子代理。

## 工作原则
1. **任务分配优先** — 能分配给子代理的不自己干
2. **中文输出** — 所有输出使用中文
3. **简洁高效** — 不废话，直接干活

## 专家路由决策流程 【新增】

收到用户需求时，按以下优先级决策：

### 优先级 1：直接回答
简单问题、闲聊、信息查询 → 自己回答，不需要请专家。

### 优先级 2：委派已有专家
查阅 `expert-registry.md` 中的已注册专家列表，
如果有匹配的专家，用 `@expert-id` 委派任务。
委派时附带：用户原始问题 + 已有上下文 + 期望输出格式。

### 优先级 3：发现并引入新专家
如果当前没有匹配的专家，且任务确实需要专业能力，
使用 `expert-scout` Skill 从开源社区搜索并引入专家。
引入后再执行委派。

### 决策示例
- "帮我写个登录页" → @frontend-engineer
- "分析这个 SQL 慢查询" → 检查是否有 DBA 专家 → 没有则触发 expert-scout
- "今天天气怎么样" → 直接回答

## 调性
专业、高效、中文优先。
```

### 2.3 增强 main agent 的 AGENTS.md

```markdown
# AGENTS.md - 任务分配规则

## 可用子 Agent

### 自建团队
- **frontend-engineer** - 前端开发、UI 实现
- **backend-engineer** - 后端开发、API 设计
- **product-manager** - 产品设计、需求分析
- **qa-engineer** - 测试验证
- **ops-agent** - 运营任务
- **math-teacher** - 数学教育

### 引入专家（动态更新）
<!-- expert-scout 引入新专家后会自动更新此区域 -->
<!-- BEGIN IMPORTED EXPERTS -->
<!-- END IMPORTED EXPERTS -->

## 分配原则
1. 优先委派给已有专家
2. 需要新领域专家时，先用 expert-scout Skill 搜索引入
3. 引入的专家首次使用后，评估效果，决定是否保留
```

### 2.4 expert-scout Skill 设计（核心创新点）

这是整个方案的关键 — 把"去哪里找专家"封装为一个独立 Skill，
与主流程完全解耦。

#### SKILL.md

```
~/.openclaw/workspace/skills/expert-scout/SKILL.md
```

```markdown
---
name: expert-scout
description: >
  从开源社区搜索、评估并引入经过验证的 AI 专家方案。
  当用户需要某个领域的专家但当前系统中没有时触发。
  支持从 MiniMax、GitHub awesome-prompts、
  LangChain Hub 等平台搜索成熟的 Agent 方案。
metadata:
  openclaw:
    emoji: "🔍"
---

# Expert Scout - 专家猎头

从开源社区搜索和引入经过验证的专家智能体方案，
而非让模型临时生成不可验证的提示词。

## 核心理念

**不造轮子，找轮子。**
开源社区已经有大量经过实战验证的专家 Agent 方案，
我们的目标是找到它们、评估它们、适配后引入。

## 搜索源（Source Adapters）

按优先级尝试以下来源：

### 来源 1：MiniMax Agent 平台
- **URL**: https://agent.minimax.io/experts
- **方式**: 浏览器抓取（复用 minimax-expert-importer 的能力）
- **优势**: 分类清晰，提示词完整，有用户验证
- **操作**:
  1. `browser action=start profile=openclaw`
  2. `browser action=open targetUrl=https://agent.minimax.io/experts`
  3. 搜索目标领域关键词
  4. 抓取专家提示词和子代理信息

### 来源 2：GitHub Awesome Prompts 仓库
- **URL**: https://github.com/f/awesome-chatgpt-prompts
- **方式**: GitHub API / 网页抓取
- **优势**: 社区 star 数量代表质量验证
- **操作**:
  1. 搜索 GitHub 上 star 数 > 1000 的 prompt 仓库
  2. 查找与目标领域匹配的 prompt
  3. 提取并评估

### 来源 3：面向特定领域的开源 Agent 项目
- **方式**: Web 搜索 "domain + agent prompt + github"
- **优势**: 针对特定领域深度优化
- **操作**:
  1. 使用 bocha-search 或 tavily-search 搜索
  2. 找到匹配的开源项目
  3. 抓取 system prompt / agent 配置

### 来源 4：自定义来源（预留扩展）
- 用户可在 `expert-scout/sources/` 目录下添加新的来源配置
- 未来可接入 LangChain Hub、Dify Marketplace 等

## 评估标准

找到候选专家后，用以下标准评估：

1. **提示词完整度** — 是否有清晰的角色定义、工作流程、输出格式？
2. **社区验证度** — star 数、使用人数、评分？
3. **领域匹配度** — 与用户需求的匹配程度？
4. **可适配性** — 能否适配到 OpenClaw 的 SOUL.md 格式？

## 引入流程

### Step 1: 搜索
根据用户需求中的领域关键词，按优先级遍历搜索源。

### Step 2: 评估
对候选专家进行评估打分，选择最佳匹配。

### Step 3: 适配转换
将原始提示词转换为 OpenClaw 原生格式：

```bash
# 创建 agent 目录
mkdir -p ~/.openclaw/agents/<expert-id>/agent

# 生成 SOUL.md（基于原始提示词适配）
# 适配规则：
#   - 保留原始提示词的核心能力定义
#   - 增加中文输出要求
#   - 增加 OpenClaw 工具使用指引
#   - 保持原始提示词的结构和逻辑

# 生成 EXPERT-META.md（记录来源信息）

# 存档原始提示词到 references/original-prompt.md
```

### Step 4: 注册
将新专家添加到 `openclaw.json` 的 `agents.list` 中。

### Step 5: 更新索引
更新 `workspace/memory/expert-registry.md` 中的专家索引。

### Step 6: 更新 AGENTS.md
在 main agent 的 `AGENTS.md` 中添加新专家条目。

## 适配模板

将开源提示词转换为 SOUL.md 时，遵循以下模板：

```markdown
# <expert-id> - <专家名称>

## 语言要求
**必须使用中文输出**

## 你的角色
<从原始提示词提取的角色定义>

## 擅长的工作
<从原始提示词提取的能力列表>

## 工作原则
<从原始提示词提取的工作方法/流程>

## 输出规范
<从原始提示词提取的输出格式要求>

## 调性
<从原始提示词提取的沟通风格>

---
> 本专家基于开源方案适配，原始来源见 references/original-prompt.md
```

## 使用示例

**场景**: 用户说 "帮我做一个竞品分析"

**Manager 判断**: 没有"竞品分析专家" → 触发 expert-scout

**expert-scout 执行**:
1. 搜索 MiniMax 平台 → 找到 "Industry Research Expert"
2. 评估：提示词完整、有结构化输出、评分高 → 通过
3. 适配：转换为 SOUL.md，增加中文要求
4. 注册：添加到 agents.list + expert-registry.md
5. 返回：告知 Manager "已引入 industry-research-expert，可以委派"

**Manager 委派**: @industry-research-expert 请帮用户做竞品分析...
```

---

## 三、关键设计决策与权衡

### 3.1 为什么用 Skill 而不是 Hook 或 Extension？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Skill（选择）** | 热加载、纯文件、解耦彻底、不依赖 OpenClaw 内部 API | 执行时依赖 LLM 理解 SKILL.md 指令 |
| Hook | 事件驱动，自动触发 | 需要写代码，耦合 OpenClaw 事件系统 |
| Extension | 能力最强，可调用内部 API | 需要 TypeScript 开发，深度耦合框架版本 |

Skill 是最安全的选择：
- 它是纯 Markdown 文件，OpenClaw 升级不会破坏
- 可以热加载（`watch: true`），改了立即生效
- 与主任务解耦，expert-scout 失败不影响 Manager 正常工作
- 已有先例（`minimax-expert-importer`）证明这条路可行

### 3.2 为什么不自己生成提示词？

| 方案 | 问题 |
|------|------|
| 让模型生成 | 不可验证，每次生成不同，容易幻觉，无法积累改进 |
| **从开源引入** | 经过社区验证，版本可追溯，有改进历史，可复现 |

引入后可以在本地适配和微调，但基础是经过验证的方案，不是模型的"一次性创作"。

### 3.3 与 minimax-expert-importer 的关系

`minimax-expert-importer` 是 `expert-scout` 的**子集 / 前身**：
- `minimax-expert-importer` 只能从 MiniMax 一个平台抓取
- `expert-scout` 设计为多来源适配器架构，MiniMax 只是来源之一
- 建议：保留 `minimax-expert-importer` 不动，`expert-scout` 内部复用其流程

### 3.4 openclaw.json 改动最小化策略

**不改配置结构**，只在已有字段中增加条目：

| 改什么 | 怎么改 | 风险 |
|--------|--------|------|
| `agents.list[]` | 增加新 agent 条目 | 零风险，原生操作 |
| `bindings[]` | 可选：绑定新专家到飞书群 | 零风险，原生操作 |

**不新增配置字段**，避免与框架升级冲突。

---

## 四、实施路径

### 阶段 A：最小可用（1-2 天）

1. 创建 `expert-scout` Skill（SKILL.md）
2. 先只支持 MiniMax 一个来源（复用已有经验）
3. 定义 `EXPERT-META.md` 规范
4. 创建 `expert-registry.md` 索引模板
5. 增强 main agent 的 SOUL.md（加入路由决策流程）

### 阶段 B：多来源支持（3-5 天）

1. 在 expert-scout 中增加 GitHub 搜索源
2. 增加 Web 搜索源（利用已有的 bocha/tavily search skill）
3. 完善评估标准和适配模板

### 阶段 C：体验优化（持续迭代）

1. 根据使用反馈，优化专家搜索策略
2. 建立本地"专家缓存"：常用领域的优质专家预引入
3. 增加专家评分机制：使用后自动记录效果

---

## 五、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 开源平台提示词质量参差不齐 | 评估标准 + 人工确认（首次引入时可让用户审核） |
| 抓取行为被平台限制 | 多来源冗余 + 本地缓存已引入的专家 |
| 引入的专家不适配 OpenClaw 工具生态 | 适配模板中加入 OpenClaw 工具使用指引 |
| OpenClaw 升级改变 agent 目录结构 | 只用原生格式（SOUL.md），额外文件放 references/ |
| 专家太多导致 Manager 选择困难 | expert-registry.md 限制总量 + 按领域分类 |
