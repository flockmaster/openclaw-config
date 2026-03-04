---
name: expert-scout
description: >
  从开源社区搜索并引入经过验证的专家智能体。当 main agent 路由决策发现
  当前团队没有匹配的专家时触发。支持从 GitHub 提示词仓库、cursor.directory、
  LangChain Hub 等来源发现专家。触发词：找专家、招募专家、引入专家、
  expert-scout、搜索专家、没有合适的专家。
metadata:
  openclaw:
    emoji: "🔍"
---

# Expert Scout - 专家猎头

从开源社区搜索经过验证的专家方案并引入为 OpenClaw Agent。
**不自己编提示词，找成熟的轮子。**

## 核心理念

模型临时生成的提示词不可验证、不可复现。
开源社区有大量经过实战检验的专家 Agent 方案，找到它们 → 评估 → 适配引入。

---

## 第一步：明确需求

收到任务时先确认：
1. **领域关键词**：用户需要什么领域的专家？（如：数据分析、安全审计、DBA）
2. **能力要求**：需要具备哪些具体能力？
3. **查重**：先读 `memory/expert-registry.md`，确认确实没有已有专家能覆盖

---

## 第二步：搜索提示词来源

### 来源可用性总结（实测结论）

| 优先级 | 来源 | 可用性 | 说明 |
|--------|------|--------|------|
| **最高** | GitHub 提示词仓库 | git clone，无需认证 | 生产级提示词，完整度最高 |
| **高** | cursor.directory | 开源 GitHub 仓库 | 编码/技术领域专家首选 |
| **中** | LangChain Hub | SDK 拉取，无需登录 | Agent 推理模板 |
| **中** | Anthropic 提示词库 | 公开网页 | 高质量但偏简单任务 |
| 低 | Web 搜索兜底 | bocha/tavily | 前面都没找到时用 |
| ❌ | MiniMax | 403/SPA，浏览器不稳定 | **实测不可靠，不要再尝试** |
| ❌ | Coze（扣子） | 配置不公开 | 无法查看他人 Agent 配置 |
| ❌ | GPTs Hunter | 仅目录，无提示词 | 只有名称和描述 |
| ❌ | Dify Marketplace | 插件/工作流，非提示词 | 不是我们要的东西 |

---

### 来源 A：GitHub 提示词仓库（首选，命中率最高）

这些仓库包含从商业 AI 产品中提取的完整生产级系统提示词，直接 clone 即可用。

#### A1. 综合型大仓库（覆盖面最广）

**danielrosehill/System-Prompt-Library**
- URL: `https://github.com/danielrosehill/System-Prompt-Library`
- 内容: **937+ 个系统提示词**，覆盖各领域（数据分析、安全、写作、项目管理、教育等）
- 格式: JSON + Markdown 双格式，**有 `consolidated_prompts.json` 可一次性获取全部**
- 质量: 实用导向，带分类元数据
- 也可通过 HuggingFace 获取: `https://huggingface.co/datasets/danielrosehill/System-Prompt-Library`

```bash
# 推荐：直接下载合并文件（最快）
curl -L -o /tmp/all-prompts.json \
  "https://raw.githubusercontent.com/danielrosehill/System-Prompt-Library/main/consolidated_prompts.json"

# 或完整 clone
git clone --depth 1 https://github.com/danielrosehill/System-Prompt-Library /tmp/system-prompt-library
# 提示词在 system-prompts/json/ 和 system-prompts/markdown/ 目录下
```

**搜索方式：**
```bash
# 在 JSON 文件中搜索领域关键词
cat /tmp/all-prompts.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
keyword = '<领域关键词>'
for p in data:
    if keyword.lower() in json.dumps(p).lower():
        print(f\"--- {p.get('title', 'N/A')} ---\")
        print(p.get('content', '')[:200])
        print()
"
```

**LouisShark/chatgpt_system_prompt** (10.3k stars)
- URL: `https://github.com/LouisShark/chatgpt_system_prompt`
- 内容: 数百个 Custom GPT 提示词 + 官方产品提示词（OpenAI、Claude、Manus 等）
- 结构: `prompts/official-product/`（生产级）、`prompts/gpts/`（社区级）
- 适合: 找特定功能的专家（如 Excel 处理、SEO、数据可视化）

```bash
git clone --depth 1 https://github.com/LouisShark/chatgpt_system_prompt /tmp/chatgpt-prompts
# 按目录浏览
ls /tmp/chatgpt-prompts/prompts/gpts/
```

#### A2. AI 编码工具提示词（技术专家参考）

**tallesborges/agentic-system-prompts**
- URL: `https://github.com/tallesborges/agentic-system-prompts`
- 内容: Claude Code、Gemini CLI、Cline、Aider 等 7 个编码 Agent 的完整提示词模板
- 质量: **最高** — 包含角色定义 + 指令 + 工具 schema
- 适合: 引入编码/架构类专家时参考提示词结构

```bash
git clone --depth 1 https://github.com/tallesborges/agentic-system-prompts /tmp/agentic-prompts
```

**x1xhlol/system-prompts-and-models-of-ai-tools**
- URL: `https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools`
- 内容: 36+ AI 工具的系统提示词（Cursor、Devin、Manus、Windsurf、v0、Replit 等）
- 质量: 生产级，从商业产品提取
- 适合: 理解顶级 Agent 的提示词架构

```bash
git clone --depth 1 https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools /tmp/ai-tool-prompts
ls /tmp/ai-tool-prompts/
```

#### A3. 其他有价值的仓库

| 仓库 | Stars | 特点 |
|------|-------|------|
| `0xeb/TheBigPromptLibrary` | 4.7k | MIT 协议，含越狱/防护提示词研究 |
| `dontriskit/awesome-ai-system-prompts` | — | 32 个 AI 工具提示词，分目录整理 |
| `EliFuzz/awesome-system-prompts` | — | 按日期版本管理，可追踪提示词演变 |
| `Piebald-AI/claude-code-system-prompts` | — | Claude Code 提示词的精细拆解 |

---

### 来源 B：cursor.directory（编码/技术类专家首选）

- URL: `https://cursor.directory/`
- GitHub 源码: `https://github.com/pontusab/cursor.directory`
- 内容: 按技术栈分类的编码提示词（TypeScript、React、Python、Next.js、Flutter、Laravel 等）
- 格式: TypeScript 文件，每个导出 `content`（提示词文本）、`author`、`url`
- 质量: 社区精选，面向生产编码场景

```bash
# clone 源码
git clone --depth 1 https://github.com/pontusab/cursor.directory /tmp/cursor-directory
# 提示词在这里
ls /tmp/cursor-directory/packages/data/rules/

# 或者用 GitHub API 列出所有规则文件
curl -s "https://api.github.com/repos/pontusab/cursor.directory/contents/packages/data/rules" \
  | python3 -c "import json,sys; [print(f['name']) for f in json.load(sys.stdin) if f['name'].endswith('.ts')]"
```

**配套仓库**: `https://github.com/PatrickJS/awesome-cursorrules` — 社区精选的 cursor rules 集合

**适用场景**: 引入前端框架专家、后端架构专家、特定语言专家时，这里的提示词质量比通用仓库更高。

---

### 来源 C：LangChain Hub（Agent 模板）

- URL: `https://smith.langchain.com/hub`
- 内容: Agent 推理模板、RAG 提示词、Chain-of-Thought 模板
- 访问: **无需登录**即可读取，发布才需要账号
- 格式: LangChain 模板格式（带 `{variables}` 占位符）

```bash
# 用 Python SDK 拉取公开提示词
pip install langchain langchain-core 2>/dev/null
python3 -c "
from langchain import hub
# 拉取指定提示词（格式：handle/prompt_name）
prompt = hub.pull('hwchase17/react')
print(prompt.template)
"
```

**注意**: LangChain Hub 的提示词偏 Agent 推理框架（ReAct、CoT），不是独立的领域专家提示词。适合参考 Agent 的思考结构，不适合直接当专家人设。

---

### 来源 D：Anthropic 提示词库（参考级）

- URL: `https://docs.anthropic.com/en/prompt-library`
- 内容: ~60 个 Anthropic 官方精选提示词
- 质量: 专业级，展示最佳实践
- 限制: 偏任务型（代码优化、翻译等），不是复杂 Agent 系统提示词

适合**参考提示词写法**，不适合直接引入为专家。

---

### 来源 E：Web 搜索兜底

前面来源都没找到合适的，再用搜索：

```bash
# bocha 搜索
node ~/.openclaw/workspace/skills/bocha-search/scripts/search.js \
  "<领域> AI agent system prompt github" --count 5 --summary

# tavily 搜索
python3 ~/.openclaw/workspace/skills/openclaw-tavily-search/scripts/tavily_search.py \
  --query "<领域> expert agent prompt open source" --max-results 5 --format md
```

---

### 不要尝试的来源（实测不可用）

| 来源 | 原因 |
|------|------|
| **MiniMax** (`agent.minimax.io`) | SPA 应用，直接访问 403，浏览器连接不稳定 |
| **Coze / 扣子** | 他人 Agent 配置完全不公开 |
| **GPTs Hunter** | 只是 GPT 名录，不展示系统提示词 |
| **Dify Marketplace** | 卖的是插件和工作流 DSL，不是提示词 |

---

## 第三步：评估候选专家

找到候选后，按以下标准打分（满分 5 分），总分 >= 12 可引入：

| 维度 | 评分标准 |
|------|---------|
| **提示词完整度** | 有角色定义+工作流程+输出格式=5, 只有角色定义=2, 一句话描述=1 |
| **社区验证度** | star>1k 或知名 AI 产品提取=5, star>100=3, 无数据=1 |
| **领域匹配度** | 完全匹配需求=5, 部分匹配=3, 勉强相关=1 |
| **可适配性** | 可直接用=5, 需少量改造=3, 需大改=1 |

评估结果记录下来，多个候选时选总分最高的。

---

## 第四步：适配转换

将原始提示词转换为 OpenClaw 原生 Agent 格式。

### 4.1 创建 Agent 目录

```bash
mkdir -p ~/.openclaw/agents/<expert-id>/agent/references
```

`<expert-id>` 命名规则：`<领域>-expert`，如 `data-analysis-expert`、`security-expert`。

### 4.2 生成 SOUL.md

存放到对应 Agent 的 **workspace** 目录（这是 OpenClaw 实际加载人设的位置）：

```bash
mkdir -p ~/.openclaw/workspace-<expert-id>
```

写入 `~/.openclaw/workspace-<expert-id>/SOUL.md`，使用以下适配模板：

```markdown
# SOUL.md - <专家名称>

*<一句话定位>*

## 用户画像

用户（刘伟）要求极其严格，半成品等于没做。

## 核心能力

<从原始提示词提取的角色定义和核心能力>

## 工作原则

<从原始提示词提取的工作方法/决策流程>

## 输出规范

<从原始提示词提取的输出格式要求。如原始无明确格式，添加：>
- 结构化输出，用 Markdown 表格和列表
- 中文回复

## 调性

<从原始提示词提取的沟通风格>

## 可用技能

⚠️ 如有相关 skill，列出并要求使用前先读取 SKILL.md。

## A2A 任务委托

**专业边界：**
- ✅ 你擅长：<领域能力列表>
- ❌ 不擅长：<明确不覆盖的领域>

**委托指南：**
- 前端 UI → @frontend-engineer
- 后端代码 → @backend-engineer
- 产品需求 → @product-manager
- 通用任务 → @main

---

## 多 Agent 协作规范

### 结果汇报格式（完成任务时必须遵守）

✅ DONE

## 产出文件
- {绝对路径}：{说明}

## 摘要
{3 句话以内}

## 后续建议（可选）
- {建议}

### 文件路径规则
- 所有文件引用必须使用绝对路径
- 跨 agent 传递的文件写到 ~/.openclaw/workspace/shared/

---

> 本专家基于开源方案适配，原始来源见 references/original-prompt.md
```

**适配要点（不是复制粘贴！）：**
1. 保留原始提示词的**核心能力定义和工作流程**
2. 增加**中文输出要求**
3. 增加**用户画像**（刘伟的严格标准）
4. 增加**A2A 协作规范**（委托指南 + 汇报格式 + 文件路径规则）
5. 增加**可用技能**引用（如有相关 skill）
6. 删除原始提示词中与 OpenClaw 不兼容的部分（如特定平台 API 调用）

### 4.3 存档原始提示词

```bash
# 原封不动存档，便于溯源和未来重新适配
cat > ~/.openclaw/agents/<expert-id>/agent/references/original-prompt.md << 'EOF'
# 原始提示词

来源：<平台/仓库名称>
URL：<原始 URL>
抓取时间：<YYYY-MM-DD>

---

<原始提示词完整内容>
EOF
```

### 4.4 生成 EXPERT-META.md

```bash
# 参考模板：~/.openclaw/workspace/notes/templates/EXPERT-META.template.md
cat > ~/.openclaw/agents/<expert-id>/agent/EXPERT-META.md
```

填写来源、质量评估、兼容性信息。

---

## 第五步：注册

### 5.1 注册到 openclaw.json

在 `agents.list` 数组中追加：

```json
{
  "id": "<expert-id>",
  "name": "<专家中文名>",
  "workspace": "/Users/tingjing/.openclaw/workspace-<expert-id>",
  "agentDir": "/Users/tingjing/.openclaw/agents/<expert-id>/agent",
  "model": "<推荐模型>",
  "memorySearch": {
    "extraPaths": [
      "/Users/tingjing/.openclaw/workspace/MEMORY.md",
      "/Users/tingjing/.openclaw/workspace/memory"
    ]
  }
}
```

模型选择建议：
- 需要深度推理的专家 → `bailian/qwen3.5-plus` 或 `bailian/kimi-k2.5`
- 通用类专家 → `bailian/glm-5`

### 5.2 更新专家索引

在 `~/.openclaw/workspace/memory/expert-registry.md` 中：
- 在 `<!-- BEGIN IMPORTED EXPERTS -->` 和 `<!-- END IMPORTED EXPERTS -->` 之间添加新行
- 更新"领域覆盖"checklist，打勾已覆盖的领域

### 5.3 更新 main agent 路由表

在 `~/.openclaw/workspace/SOUL.md` 的引入专家区域：
- 在 `<!-- BEGIN IMPORTED EXPERTS -->` 和 `<!-- END IMPORTED EXPERTS -->` 之间添加：
  ```
  | <领域描述> | `<expert-id>` |
  ```

---

## 第六步：验证与交付

1. 确认文件结构完整：
   - `workspace-<expert-id>/SOUL.md` 存在且内容合理
   - `agents/<expert-id>/agent/EXPERT-META.md` 存在
   - `agents/<expert-id>/agent/references/original-prompt.md` 存在
2. 确认 `openclaw.json` 中注册成功
3. 确认 `expert-registry.md` 已更新
4. 确认 `workspace/SOUL.md` 路由表已更新
5. 向 main agent 报告：
   > "已引入 `<expert-id>`（<专家名称>），擅长 <领域>，可以用 `@<expert-id>` 委派任务。"

---

## 示例：引入数据分析专家

**触发**：用户说"帮我分析这份销售数据"，main 发现没有数据分析专家

**执行**：
1. 下载 `danielrosehill/System-Prompt-Library` 的 `consolidated_prompts.json`
2. 搜索 "data analysis" 关键词 → 找到多个数据分析相关提示词
3. 评估最佳匹配：完整度 4 + 验证度 3 + 匹配度 5 + 适配性 4 = 16 ✅
4. 适配：提取核心能力 + 加中文要求 + 加协作规范 → 写入 `workspace-data-analysis-expert/SOUL.md`
5. 存档原始提示词到 `references/original-prompt.md`
6. 注册到 `openclaw.json` + `expert-registry.md` + `SOUL.md` 路由表
7. 交付："已引入 `data-analysis-expert`，可以 `@data-analysis-expert` 委派"

---

## 本地提示词库（推荐预下载）

为了加速搜索，建议一次性 clone 核心仓库到本地：

```bash
# 创建本地提示词库目录
mkdir -p ~/.openclaw/workspace/prompt-library

# 下载核心仓库（只需做一次）
git clone --depth 1 https://github.com/danielrosehill/System-Prompt-Library \
  ~/.openclaw/workspace/prompt-library/system-prompt-library

git clone --depth 1 https://github.com/LouisShark/chatgpt_system_prompt \
  ~/.openclaw/workspace/prompt-library/chatgpt-system-prompt

git clone --depth 1 https://github.com/pontusab/cursor.directory \
  ~/.openclaw/workspace/prompt-library/cursor-directory
```

预下载后，搜索速度从"网络请求"变为"本地文件搜索"，几秒出结果。

---

## 与 minimax-expert-importer 的关系

`minimax-expert-importer` 是本 Skill 的前身，专注 MiniMax 单一来源。
实测 MiniMax 平台抓取不稳定（403/SPA/浏览器连接问题），本 Skill 已切换到 GitHub 仓库为主要来源。
两个 Skill 共存不冲突，但建议优先使用 expert-scout。
