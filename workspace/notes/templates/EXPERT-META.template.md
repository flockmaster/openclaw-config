# Expert Metadata

> 引入专家的"身份证"，记录来源、质量、兼容性信息。
> 存放位置：`~/.openclaw/agents/<expert-id>/agent/EXPERT-META.md`

## 来源

- **平台**: minimax / github / web-search / custom
- **原始名称**: <平台上的原始专家名称>
- **原始 URL**: <抓取来源的完整 URL>
- **引入时间**: YYYY-MM-DD
- **引入方式**: expert-scout skill

## 质量评估

- **评分明细**:
  - 提示词完整度: X/5
  - 社区验证度: X/5
  - 领域匹配度: X/5
  - 可适配性: X/5
  - **总分: XX/20**
- **验证状态**: verified / unverified / adapted
  - `verified` = 原始提示词直接可用，几乎无改动
  - `adapted` = 基于原始提示词做了本地化适配（大部分引入专家应为此状态）
  - `unverified` = 未经测试，仅初步引入
- **适配说明**: <描述做了哪些本地化改动，如增加中文要求、协作规范等>

## 使用记录

- **使用次数**: 0
- **最近使用**: —
- **效果评价**: 待评估

## 兼容性

- **OpenClaw 版本**: <引入时的 OpenClaw 版本，如 2026.2.24>
- **依赖 Skills**: <列出该专家工作时需要的 skill，如 bocha-search, clean-code>
- **推荐模型**: <如 bailian/qwen3.5-plus>
- **模型选择理由**: <如"需要长上下文推理能力">
