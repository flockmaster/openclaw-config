# 已导入 MiniMax 专家索引

> 最后更新: 2026-02-28

## 产品设计类

| 专家名称 | 浏览量 | 状态 | 本地路径 |
|----------|--------|------|----------|
| Landing Page Builder | 40,434 | ✅ 已抓取 | minimax-experts/product-design.md |
| PRD Assistant | 2,512 | ✅ 已抓取 | minimax-experts/product-design.md |
| ui-ux-designer | 727 | ⏳ 待抓取 | - |
| SaaS niche finder | 1,235 | ⏳ 待抓取 | - |

## 前端开发类

| 专家名称 | 浏览量 | 状态 | 本地路径 |
|----------|--------|------|----------|
| PPTX Maker | 35,144 | ✅ 已抓取 | minimax-experts/frontend.md |
| Landing Page Builder | 40,434 | ✅ 已抓取 | minimax-experts/product-design.md |
| Visual Lab | 10,100 | ⏳ 待抓取 | - |
| Principle Animator | 3,378 | ⏳ 待抓取 | - |

## 后端开发类

| 专家名称 | 浏览量 | 状态 | 本地路径 |
|----------|--------|------|----------|
| Industry Research Expert | 10,614 | ✅ 已抓取 | minimax-experts/backend.md |
| ClickHouse Best Practices | 2,933 | ⏳ 待抓取 | - |
| AI Agents Architect | 411 | ⏳ 待抓取 | - |
| Mini Coder Max | 1,683 | ⏳ 待抓取 | - |

## 数据分析类

| 专家名称 | 浏览量 | 状态 | 本地路径 |
|----------|--------|------|----------|
| Multi-Agent Trading | 9,864 | ⏳ 待抓取 | - |
| Excel Processor | 9,730 | ⏳ 待抓取 | - |

---

## 抓取方法总结

### 成功经验

1. **浏览器模式选择**
   - 使用 `profile=openclaw` 独立浏览器，不依赖用户手动连接
   - 绕过 Fake-IP 检测问题

2. **页面交互模式**
   ```
   snapshot → click(expert-card) → snapshot → extract → close-panel → repeat
   ```

3. **关键数据提取**
   - 项目指令：完整的 System Prompt
   - 子代理列表：多代理协作的子代理名称
   - 作者和浏览量：用于评估专家质量

4. **存储结构**
   - 按类别分文件存储
   - 保留完整提示词，便于后续创建本地 Agent

### 踩坑记录

1. **refs 动态变化**：每次交互后需要重新 snapshot
2. **面板管理**：需要关闭当前面板才能点击下一个专家
3. **时间成本**：每个专家约需 30-60 秒完整抓取

---

*持续更新中...*