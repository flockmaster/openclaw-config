# Skill 分配分析报告

**生成时间:** 2026-02-27 15:36 GMT+8  
**目标:** 分析已安装的 skill 和各 Agent 的 skill 配置，排查分配不合理情况，划分全局/专属 skill。

---

## 一、当前配置状态

### 1.1 已安装的 Skill（全局目录）

**路径:** `/Users/tingjing/.openclaw/workspace/skills/`

| Skill 名称 | 功能描述 |
|------------|----------|
| `backend-patterns` | 后端架构模式、API 设计、数据库优化（Node.js/Express/Next.js） |
| `bocha-search` | 博查搜索 API 插件（网页搜索） |
| `clean-code` | 简洁编程规范（无过度工程化） |
| `flutter` | Flutter 应用构建（状态管理、widget 陷阱处理） |
| `prd` | 产品需求文档（PRD）撰写、用户故事、验收标准 |
| `proactive-agent` | 主动型 Agent 架构（记忆、反向提示、自修复） |
| `responsive-design` | 响应式设计原则 |
| `shadcn-ui` | shadcn/ui 组件库、Tailwind CSS、react-hook-form |
| `tailwindcss` | Tailwind CSS 实用类、响应式设计、深色模式 |
| `test-master` | 测试框架（单元测试、集成测试、E2E、性能测试） |
| `ui-ux-design` | UI/UX 设计原则、模式、可访问性（WCAG） |

### 1.2 Agent 列表与当前配置

| Agent ID | Agent 名称 | 工作空间 | 配置的 Model |
|----------|------------|----------|--------------|
| `main` | 主代理 | `/Users/tingjing/.openclaw/workspace` | 默认 ( Claude Opus 4.6 ) |
| `math-teacher` | 数学老师 | `/Users/tingjing/.openclaw/workspace-math-teacher` | Kimi K2.5 |
| `product-manager` | 产品经理 | `/Users/tingjing/.openclaw/workspace-product-manager` | Qwen3-Coder-Plus |
| `frontend-engineer` | 前端开发工程师 | `/Users/tingjing/.openclaw/workspace-frontend-engineer` | Kimi K2.5 |
| `backend-engineer` | 后端开发工程师 | `/Users/tingjing/.openclaw/workspace-backend-engineer` | GPT-5.3 Codex |
| `ops-agent` | 运营专家 | `/Users/tingjing/.openclaw/workspace-ops-agent` | Qwen3-Coder-Next |
| `qa-engineer` | QA 测试工程师 | `/Users/tingjing/.openclaw/workspace-qa-engineer` | Qwen3.5-Plus |
| `gpt5-tester` | 模型测试专家 | `/Users/tingjing/.openclaw/workspace-gpt5-tester` | GPT-5.3 Codex |

---

## 二、存在的问题（基于参考分类）

### 2.1 未明确配置 Skill 的 Agent

| Agent | 问题 |
|-------|------|
| `math-teacher` | 无专用 skill，应添加数学/教育相关 |
| `product-manager` | 无专用 skill，**已安装 `prd` skill 但未绑定** |
| `frontend-engineer` | 无专用 skill，**已安装 `shadcn-ui`、`tailwindcss`、`ui-ux-design`、`flutter` 但未绑定** |
| `backend-engineer` | 无专用 skill，**已安装 `backend-patterns` 但未绑定** |
| `ops-agent` | 无专用 skill |
| `qa-engineer` | 无专用 skill，**已安装 `test-master` 但未绑定** |
| `gpt5-tester` | 无专用 skill |

### 2.2 可能重复配置的 Skill（全局安装但应专属）

| Skill | 分析 |
|-------|------|
| `proactive-agent` | 适用于所有 Agent（全局） |
| `clean-code` | 通用编程规范（全局） |
| `responsive-design` | 通用设计原则（全局） |
| `ui-ux-design` | **前端专属**（但可能被其他团队模糊使用）|

### 2.3 应该全局共享但未配置的 Skill

| Skill | 当前状态 | 应对所有 Agent 可用 |
|-------|----------|-------------------|
| `bocha-search` | ✅ 已安装 | 搜索能力 |
| `clean-code` | ✅ 已安装 | 编码规范 |
| `proactive-agent` | ✅ 已安装 | 自我改进 |
| `responsive-design` | ✅ 已安装 | 响应式设计 |

---

## 三、Skill 分配建议

### 3.1 全局 Shared Skills（默认加载）

**原则：** 通用工具类、跨领域能力

| Skill | 加载建议 | 理由 |
|-------|---------|------|
| `bocha-search` | ✅ Global | 搜索是通用能力 |
| `clean-code` | ✅ Global | 编码规范普适 |
| `proactive-agent` | ✅ Global | Agent 自我改进 |
| `responsive-design` | ✅ Global | 设计基础 |

**建议配置:**
```json
{
  "agents": {
    "defaults": {
      "skills": {
        "shared": [
          "bocha-search",
          "clean-code",
          "proactive-agent",
          "responsive-design"
        ]
      }
    }
  }
}
```

### 3.2 专属 Skills（按 Agent 分配）

| Agent | 专属 Skills | 理由 |
|-------|------------|------|
| `product-manager` | `prd`, `ui-ux-design` | 需求分析、PRD 撰写、UI/UX 设计 |
| `frontend-engineer` | `shadcn-ui`, `tailwindcss`, `flutter` | UI 实现、组件库、跨平台 |
| `backend-engineer` | `backend-patterns`, `clean-code` | API 设计、后端架构 |
| `qa-engineer` | `test-master` | 测试框架、自动化测试 |
| `ops-agent` | `proactive-agent` | 自动化运维任务 |
| `math-teacher` | `search` (需确认) | 教育研究 |
| `gpt5-tester` | `test-master` | 新模型测试 |

### 3.3 建议新增的专属 Skill

| Agent | 建议 Skill | 来源 |
|-------|-----------|------|
| `math-teacher` | `math-tutor` (未安装) | 新建或从其他项目迁移 |

---

## 四、优化实施步骤

### 4.1 创建 Agent-specific Skills 目录（可选）

**方案 A：保留全局目录，使用配置绑定**

```json
// openclaw.json
{
  "agents": {
    "defaults": {
      "skills": {
        "shared": ["bocha-search", "clean-code", "proactive-agent"]
      }
    },
    "list": [
      {
        "id": "product-manager",
        "skills": {
          "exclusive": ["prd", "ui-ux-design"]
        }
      }
    ]
  }
}
```

### 4.2 修改后的配置示例

```json
{
  "agents": {
    "defaults": {
      "skills": {
        "shared": [
          "bocha-search",
          "clean-code",
          "proactive-agent"
        ]
      }
    },
    "list": [
      {
        "id": "main",
        "skills": {
          "shared": []
        }
      },
      {
        "id": "product-manager",
        "skills": {
          "shared": [],
          "exclusive": ["prd"]
        }
      },
      {
        "id": "frontend-engineer",
        "skills": {
          "shared": [],
          "exclusive": ["shadcn-ui", "tailwindcss", "flutter"]
        }
      },
      {
        "id": "backend-engineer",
        "skills": {
          "shared": [],
          "exclusive": ["backend-patterns"]
        }
      },
      {
        "id": "qa-engineer",
        "skills": {
          "shared": [],
          "exclusive": ["test-master"]
        }
      },
      {
        "id": "ops-agent",
        "skills": {
          "shared": [],
          "exclusive": []
        }
      }
    ]
  }
}
```

### 4.3 具体操作命令

```bash
# 1. 备份当前配置
cp /Users/tingjing/.openclaw/openclaw.json /Users/tingjing/.openclaw/openclaw.json.bak

# 2. 编辑配置文件（使用 jq 工具）
# 添加 skills 配置到 defaults
jq '.agents.defaults.skills = {"shared": ["bocha-search", "clean-code", "proactive-agent"]}' /Users/tingjing/.openclaw/openclaw.json > /tmp/tmp.json && mv /tmp/tmp.json /Users/tingjing/.openclaw/openclaw.json

# 3. 重启 OpenClaw 服务
openclaw gateway restart
```

---

## 五、总结

### 当前状态总结

- ✅ **已安装 11 个 Skill**，覆盖搜索、编码、UI、测试等领域
- ❌ **未配置绑定关系**，所有 Skill 全局可访问
- ❌ **缺少专属分配**，Agent 功能不明确

### 优化目标

| 目标 | 当前 | 目标状态 |
|------|------|----------|
| 全局共享 Skills | 无 | `bocha-search`, `clean-code`, `proactive-agent` |
| 专属 Skills | 无 | 按 Agent 配置专属技能 |
| 可发现性 | 低 | 通过技能绑定明确职责 |

### 下一步行动

1. **确认 Skill 绑定方案**（是否使用 `shared`/`exclusive` 配置）
2. **更新 `openclaw.json`** 添加 skills 配置
3. **更新各 Agent 的 SOUL.md** 明确技能权限
4. **测试配置**重启并验证

---

## 六、附录：完整 Skill 矩阵（推荐配置）

| Agent | 全局 Skills | 专属 Skills | 备注 |
|-------|------------|------------|------|
| `main` | `bocha-search`, `clean-code`, `proactive-agent` | - | 主代理，通用能力 |
| `math-teacher` | `bocha-search` | - | 教育专用，可能需要新 skill |
| `product-manager` | `bocha-search`, `clean-code` | `prd`, `ui-ux-design` | PRD 和 UI/UX |
| `frontend-engineer` | `bocha-search`, `clean-code` | `shadcn-ui`, `tailwindcss`, `flutter` | UI 实现 |
| `backend-engineer` | `bocha-search`, `clean-code` | `backend-patterns` | 后端架构 |
| `qa-engineer` | `bocha-search`, `clean-code` | `test-master` | 测试自动化 |
| `ops-agent` | `bocha-search`, `clean-code`, `proactive-agent` | - | 运维自动化 |
| `gpt5-tester` | `bocha-search`, `clean-code` | `test-master` | 模型测试 |

---

**报告完成时间:** 2026-02-27 15:36 GMT+8  
**生成工具:** @ops-agent (Ops Agent)  
**关联配置:** `/Users/tingjing/.openclaw/workspace/skill-分配分析报告.md`
