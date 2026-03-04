# 专家提示词来源调研报告

> 调研时间：2026-03-02
> 目的：找到真正能提供成熟 Agent 提示词的平台，避免 expert-scout 执行时无头苍蝇乱撞

## 结论

GitHub 开源仓库是唯一可靠的高质量来源。其他平台（MiniMax、Coze、GPTs Hunter、Dify）均不可用。

## 平台详细评估

### 可用（推荐）

| 平台 | URL | 内容量 | 质量 | 访问方式 |
|------|-----|--------|------|---------|
| danielrosehill/System-Prompt-Library | github.com/danielrosehill/System-Prompt-Library | 937+ 提示词 | 实用，带元数据 | git clone / JSON API |
| LouisShark/chatgpt_system_prompt | github.com/LouisShark/chatgpt_system_prompt | 数百个 GPT 提示词 | 混合（官方级 + 社区级） | git clone |
| tallesborges/agentic-system-prompts | github.com/tallesborges/agentic-system-prompts | 7 个编码 Agent | 最高（含工具 schema） | git clone |
| x1xhlol/system-prompts-and-models-of-ai-tools | github.com/x1xhlol/system-prompts-and-models-of-ai-tools | 36+ AI 工具 | 生产级 | git clone |
| cursor.directory | github.com/pontusab/cursor.directory | 技术栈分类 | 编码场景精选 | git clone / GitHub API |
| LangChain Hub | smith.langchain.com/hub | Agent 模板 | 变量模板，非独立人设 | Python SDK |
| Anthropic Prompt Library | docs.anthropic.com/en/prompt-library | ~60 个 | 专业但偏简单 | 公开网页 |

### 不可用（已验证）

| 平台 | URL | 不可用原因 |
|------|-----|-----------|
| MiniMax Agent | agent.minimax.io/experts | SPA 应用，403，浏览器连接不稳定 |
| Coze（扣子） | coze.com/store/bot | 他人 Agent 配置完全不公开 |
| GPTs Hunter | gptshunter.com | 仅目录（名称+描述），不展示系统提示词 |
| Dify Marketplace | marketplace.dify.ai | 卖插件和工作流 DSL，不是提示词 |

## 核心仓库推荐预下载

```bash
mkdir -p ~/.openclaw/workspace/prompt-library
git clone --depth 1 https://github.com/danielrosehill/System-Prompt-Library ~/.openclaw/workspace/prompt-library/system-prompt-library
git clone --depth 1 https://github.com/LouisShark/chatgpt_system_prompt ~/.openclaw/workspace/prompt-library/chatgpt-system-prompt
git clone --depth 1 https://github.com/pontusab/cursor.directory ~/.openclaw/workspace/prompt-library/cursor-directory
```
