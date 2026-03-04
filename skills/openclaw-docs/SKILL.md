# openclaw-docs - OpenClaw 文档查询

> 当任何 agent 需要查询 OpenClaw 相关问题时使用此 skill。

## 触发条件
- 需要查询 OpenClaw 配置、方法、命令等问题
- 不确定某个功能如何实现时

## 使用方法

### 1. 查询文档索引
先获取 llms.txt 解析出文档列表，根据关键词匹配相关文档。

```bash
curl -s "https://docs.openclaw.ai/llms.txt" | grep -i "关键词"
```

### 2. 读取文档内容
找到匹配的文档后，用 web_fetch 读取内容：

```bash
web_fetch url="https://docs.openclaw.ai/xxx.md" maxChars=8000
```

### 3. 返回答案
从文档中提取答案，返回：
- 核心答案（TL;DR）
- 原文链接

## 示例

**用户问题：** "怎么做 cron 定时任务？"

**处理流程：**
1. `curl -s "https://docs.openclaw.ai/llms.txt" | grep -i cron`
2. 找到相关文档：`Cron Jobs`, `Cron vs Heartbeat`, `cli/cron.md`
3. 读取 `https://docs.openclaw.ai/automation/cron-jobs.md`
4. 返回答案 + 链接

## 注意事项
- 优先读取最相关的文档
- 返回答案要简洁，附上原文链接
- 如果找不到匹配，尝试用更宽泛的关键词