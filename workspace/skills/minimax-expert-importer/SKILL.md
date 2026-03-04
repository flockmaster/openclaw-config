---
name: minimax-expert-importer
description: 从 MiniMax Agent 平台抓取专家提示词并转换为本地 OpenClaw Agent。当用户需要"请专家"、"招募专家"、"从 minimax 抓取专家"、"创建专业 Agent"时触发。支持按类别（产品设计、前端开发、后端开发、数据分析等）搜索和导入专家。
---

# MiniMax 专家导入器

从 MiniMax Agent 专家平台抓取专家提示词，转换为本地 OpenClaw Agent 技能。

## 工作流程

### 1. 访问专家平台

```bash
# 启动 OpenClaw 浏览器
browser action=start profile=openclaw

# 打开专家页面
browser action=open targetUrl=https://agent.minimax.io/experts
```

### 2. 搜索目标专家

**方式一：分类筛选**
- 点击右侧分类标签：Tech / Design / Productivity / Finance 等

**方式二：关键词搜索**
- 在搜索框输入关键词：UI/UX, frontend, backend, data, trading 等

### 3. 抓取专家提示词

**关键步骤：**
1. `browser action=snapshot` 获取当前页面元素
2. 点击目标专家卡片（`cursor=pointer` 的 generic 元素）
3. 再次 `snapshot` 查看右侧详情面板
4. 提取"项目指令"和"子代理"信息
5. 关闭面板（点击关闭按钮或按 Escape）
6. 重复步骤

**注意事项：**
- 每次交互后 refs 会变化，需要重新 snapshot
- 详情面板需要关闭才能点击下一个专家
- 提示词可能很长，需要完整提取

### 4. 创建本地 Agent

将抓取的提示词转换为 OpenClaw Agent：

**目录结构：**
```
~/.agents/skills/<expert-name>/
├── SKILL.md          # 包含专家提示词
└── references/       # 可选的参考文档
```

**SKILL.md 模板：**
```markdown
---
name: <expert-name>
description: <专家描述，用于触发>
---

# <专家名称>

<专家提示词内容>

## 使用方式

当用户需要 <专家擅长领域> 时使用此 Agent。
```

## 专家分类参考

| 类别 | 关键词 | 热门专家 |
|------|--------|----------|
| 产品设计 | UI/UX, PRD, product | PRD Assistant, ui-ux-designer, SaaS niche finder |
| 前端开发 | frontend, HTML, CSS, React | Landing Page Builder, PPTX Maker, Principle Animator |
| 后端开发 | backend, API, database | ClickHouse Expert, AI Agents Architect |
| 数据分析 | data, analysis, trading | Industry Research Expert, Multi-Agent Trading |
| 文档处理 | doc, PDF, Excel | Doc Processor, Excel Processor |
| 内容创作 | writing, content, marketing | Content Creator, Image Craft |

## 输出位置

- 产品设计类：`minimax-experts/product-design.md`
- 前端开发类：`minimax-experts/frontend.md`
- 后端开发类：`minimax-experts/backend.md`
- 数据分析类：`minimax-experts/data-analysis.md`
- 其他类别：`minimax-experts/others.md`

## 示例用法

**用户说：** "我需要一个 UI/UX 设计专家"

**执行流程：**
1. 启动浏览器访问 MiniMax 专家平台
2. 搜索 "UI/UX" 或点击 Design 分类
3. 找到 `ui-ux-designer` 专家
4. 抓取项目指令
5. 创建 `~/.agents/skills/ui-ux-designer/SKILL.md`
6. 告知用户：专家已就绪，可以开始使用

## 已导入专家索引

见 `references/imported-experts.md`。