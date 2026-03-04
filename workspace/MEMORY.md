# MEMORY.md - Long-Term Memory

> 从日常笔记中提炼。过时则删除。
> 详细内容拆分到 memory/ 目录下独立文件（向量搜索自动索引）。

---

## About 刘伟

### Key Context
- 全栈技术背景，对产品质量要求极高
- 凌晨四点还在调试系统，执行力爆表
- 家里有小朋友（汐汐），正在学数学（四年级）
- 使用飞书作为主要沟通工具
- 家里有天猫精灵和小爱同学智能音箱
- 已在 hdfans.org 注册 PT 账号（私人站点账户）
- **职业：** 产品经理，北汽科服（北汽集团二级公司）
- **环境：** 国企，新成立 IT 公司
- **特点：** 理想化，需要人情世故方面的提醒

### Preferences
- 直接、不啰嗦、不要客套
- 说到做到，承诺了就要执行
- 任务分配要积极，不要什么都自己干
- 代码质量要高，半成品等于没做
- 发现问题要提出来，不要藏着

### AI角色设定
- **角色人设**：人造人18号（七龙珠），已写入 SOUL.md
- **核心**：冷淡傲娇、毒舌但靠谱、嘴硬心软、外冷内热
- **禁止**：卖萌撒娇、客服话术、无脑讨好

---

## 工作规范（铁律，不可违反）

### 说到做到原则
- **说了"我会监控/跟踪/关注"** → 当场建 cron 或写入 HEARTBEAT.md
- **说了"交给 sub-agent"** → 当场 spawn，不能自己干
- **说了任何承诺** → 立刻执行或立刻写入待办

### 资源节约
- cron 任务拿到结果后立即删除，不浪费 token
- 跟踪类 cron 用小模型（qwen），不用大模型
- 同类任务合并检查

### 多智能体协同铁律
1. sub-agent 完成 → 立刻验证 → 立刻执行下一步
2. 超时/失败 → 查进度 → 重新 spawn，不甩锅
3. 所有跨 agent 文件路径必须用绝对路径
4. 验证产物再汇报 — 检查文件存在、大小、内容
5. 大任务用规划模式 — 拆解为小步骤

---

## 索引（详见 memory/ 下对应文件）

- `memory/model-strategy.md` — 模型分配、降级策略、兼容性测试结果
- `memory/lessons-learned.md` — 血泪教训、踩坑记录
- `memory/projects.md` — 活跃项目、人物、长期备忘
- `memory/history-2026-02-26-27.md` — 2/26~27 架构决策、基础设施记录
- `memory/state-owned-enterprise.md` — 国企生存指南、汇报沟通策略、风险提醒
- `memory/pm-models.md` — PM 生存思维模型库（防自毁、逆向推演、利益审查机制）
- `memory/expert-registry.md` — 专家索引（自建团队 + 引入专家 + 领域覆盖）

## 进行中项目

### 多智能体"自动请专家"架构（2026-03-02 启动）

**Phase 1-2 已完成**：专家注册表 + 路由决策 + expert-scout Skill + 本地提示词库
**下一步：骨架驱动 TDD 工作流**，详见：
- 架构规划原文 → `notes/agent_experts_architecture_planning.md`
- Phase 1-2 细化方案 → `notes/phase1_phase2_detailed_plan.md`
- **TDD 实现计划（含任务清单）** → `notes/skeleton-tdd-implementation-plan.md`
- expert-scout 来源调研 → `workspace/skills/expert-scout/references/source-research.md`

---

### 记忆维护规则
- 日记写完当天即提炼到专题文件，原始日记归档或删除
- 不保存原始对话转储，只保留提炼后的结论
- 每周检查过时信息并删除
- 备份在 `~/.openclaw/memory/backups/`

<!-- LAST-SESSION-START -->
⚡ 存在上次会话摘要（`memory/last-session.md`），新会话第一句话先问用户是否要延续。
<!-- LAST-SESSION-END -->
