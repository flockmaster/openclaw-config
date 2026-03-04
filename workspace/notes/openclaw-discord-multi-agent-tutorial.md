# 文章完整总结：OpenClaw + Discord 多智能体协作

### 标题
《我花了 48 小时放弃 Telegram，把 6 个 AI 员工装进 Discord，一人公司彻底自动化了》

### 作者
SoSME的Lab，2026年2月25日

---

## 一、核心问题：为什么用 AI 越用越累？

**现状**：
- 每天打开十几个网页标签，在窗口 A 让 ChatGPT 写代码，在窗口 B 让 Claude 润色文案，再打开 Midjourney 生成配图
- 用户成了 AI 之间的"人工数据搬运工"
- 这叫"工具使用者"，不叫"一人公司"

**解决方案**：
- 把散落在各个网页里的 AI，装进一栋"可以互联互通的虚拟办公大楼"
- 使用 OpenClaw 作为核心网关工具

---

## 二、为什么选 Discord 不选 Telegram？

| 维度 | Telegram | Discord |
|------|----------|---------|
| **组织架构** | 平行群聊，无法分类 | 频道分类，可建部门工位 |
| **机器人"视力"** | 隐私模式导致互相看不见 | 开权限后可读取上下文 |
| **打扰程度** | 多机器人同时回复炸屏 | Thread 机制，干完即焚 |

**结论**：从"手机通讯录"到"企业级自动化 OA 系统"的跨越

---

## 三、基建期：搭建 Discord 环境

### 第一步：建立服务器
1. 下载 Discord 客户端
2. 点击左侧绿色【+号】→【亲自创建】→【仅供我和我的朋友使用】
3. 命名为"AI 自动化总部"

### 第二步：创建 Bot（前台）
1. 打开 Discord Developer Portal (discord.com/developers/applications)
2. 点击【New Application】，取名"Main管家"
3. 左侧菜单点击【Bot】
4. 点击【Reset Token】，复制并保存 Token

### 第三步：开启特权意图
在 Bot 页面向下拉，找到【Privileged Gateway Intents】：
- 打开 **Message Content Intent**（获取消息内容）
- 打开 **Server Members Intent**（获取群成员）
- 点击"Save Changes"

**⚠️ 踩坑**：不打开的话 AI 看不到任何消息

### 第四步：邀请 Bot 进群
1. 左侧菜单点击【OAuth2】
2. Scopes 面板勾选【bot】和【applications.commands】
3. Bot Permissions 勾选相应权限
4. 复制生成的链接，粘贴到浏览器授权

---

## 四、配置期：OpenClaw 核心配置

### 结构一：Agents（大脑）
定义 AI 员工的性格和办公桌：

```json
"agents": {
  "list": [
    {
      "id": "main",
      "model": "bailian/qwen3.5-plus",
      "workspace": "~/.openclaw/workspace"
    },
    {
      "id": "dev",
      "model": "zai/glm-5",
      "workspace": "~/.openclaw/workspace-dev"
    }
  ]
}
```

### 结构二：Accounts（躯壳）
塞入 Discord Bot Token：

```json
"channels": {
  "discord": {
    "accounts": {
      "main": {
        "enabled": true,
        "token": "MTQ3NTExMjA0MTc2NDM2MDM5NQ.GaY5qO..."
      },
      "dev": {
        "enabled": true,
        "token": "MTQ3NTExMDM1Mzc1ODE5NTk1OQ.GwiBrC..."
      }
    }
  }
}
```

### 结构三：Bindings（附体）
绑定大脑和躯壳：

```json
"bindings": [
  {
    "agentId": "main",
    "match": { "channel": "discord", "accountId": "main" }
  },
  {
    "agentId": "dev",
    "match": { "channel": "discord", "accountId": "dev" }
  }
]
```

---

## 五、权限配置：打通协作

### 权限一：sessions_send（内部电话）
让 AI 之间能直接通信：

```json
"tools": {
  "agentToAgent": {
    "enabled": true,
    "allow": ["main", "content", "dev", "design", "pm"]
  }
}
```

### 权限二：sessions_spawn（影分身）
让 Agent 能召唤分身干活：

```json
{
  "id": "main",
  "subagents": {
    "allowAgents": ["content", "dev", "design", "pm"]
  },
  "tools": {
    "allow": ["*"]
  }
}
```

---

## 六、踩坑指南

### 坑位一：配对验证
**现象**：机器人回复 "Unrecognized sender. Pairing code: 839211"

**解决**：
```bash
openclaw pairing approve discord 839211
```

### 坑位二：机器人刷屏
**现象**：多个机器人同时在群里回复

**解决**：给每个账号加 `"requireMention": true`

---

## 七、实战效果

### 场景一：sessions_send（跨部门电话）

用户："@Main大管家，把这份需求表传给开发组"

Main（底层日志）：
```
[底层日志] 🛠️ Main 独立调用了 sessions_send 给 Agent: dev 拨打了专线电话
```

Main（回复）：
"老板，我已经成功跨部门连线，把项目卷宗全部丢给 Dev 了！"

### 场景二：sessions_spawn（影分身）

用户："派两个分身：1号写2000字草稿，2号画配图。在后台跑，不要阻塞聊天"

Main（回复）：
"指令收到！已释放 2 个后台影分身。老板，咱们继续聊。"

10分钟后：
"叮叮！影分身已完成！文档和配图已保存。"

---

## 八、核心价值

**异步协作与时间折叠**：
- 从"打字兼复制员"蜕变成"端坐在落地窗前喝着茶的总设计师"
- 分门别类的办公室（Discord 频道）
- 各司其职的部门名将（Agent 定向加载特定模型）
- 只需发大指令，管家会自动调度

---

## 九、配置要点总结

1. **每个 Agent 需要独立的 Bot Token**（Discord 多账号）
2. **agentToAgent 必须显式开启**才能让 AI 互相对话
3. **subagents.allowAgents** 决定谁能被召唤
4. **requireMention: true** 防止刷屏
5. **pairing 验证**是安全机制，不是 bug

---

## 十、飞书单账号 vs Discord 多账号 对比

| 维度 | Discord 多账号模式 | 飞书单账号模式（当前） |
|------|-------------------|----------------------|
| Agent 身份 | 每个 Agent = 独立机器人 | 所有 Agent 共用一个机器人 |
| 机器人头像/名字 | 各不相同 | 统一 |
| 协作机制 | sessions_send 可"互打电话" | sessions_send 无意义（自己发自己） |
| 路由方式 | accountId 路由 | 群 ID（peer.id）路由 |
| 适用场景 | 多部门协作 | 单机器人多群服务 |

---

## 十一、飞书单账号模式下的优化建议

由于飞书创建多个应用审批流程繁琐，建议采用 **spawn 协作模式**：

1. **main 作为总调度**
   - `subagents.allowAgents: ["*"]`
   - 接收用户指令后 spawn 任务给专业 Agent

2. **专业 Agent 作为执行者**
   - frontend-engineer、backend-engineer、ops-agent 等
   - 完成后主动汇报结果给 main

3. **不需要开启 agentToAgent**
   - 单账号模式下 sessions_send 没有实际意义
   - 通过 spawn + 汇报机制实现协作

---

*来源：微信公众号文章 https://mp.weixin.qq.com/s/jISSGKwPQp0_p8MBkzEC7w*