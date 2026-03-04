---
name: aetherfile
description: AI 文件归档助手。支持文件上传归档、RAG 知识库问答、语义搜索。当用户提到"文件归档"、"搜索文档"、"文件问答"、"知识库"时激活。
user-invocable: true
metadata: {"openclaw": {"emoji": "📂"}}
---

# AetherFile Skill

AI 文件归档助手，集成到 OpenClaw 中。通过 HTTP API 调用本地 AetherFile 后端。

## Backend

- 地址: `http://127.0.0.1:8788`
- 项目路径: `/Users/tingjing/Downloads/aetherfile---ai-桌面归档助手`

如果后端未运行，先启动：
```bash
cd /Users/tingjing/Downloads/aetherfile---ai-桌面归档助手/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8788
```

## 使用方式

所有操作通过 exec 工具调用 curl 完成。

### 文件上传归档

```bash
curl -s -X POST http://127.0.0.1:8788/upload -F "file=@/path/to/file.pdf"
```

响应: `{ "file_id": "xxx", "filename": "file.pdf", "chunk_count": 42 }`

上传后文件会自动解析（PDF/DOCX/TXT）、分块、向量化，进入知识库。

### RAG 知识库问答

```bash
curl -s -X POST http://127.0.0.1:8788/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "用户的问题"}'
```

响应: `{ "answer": "AI 回答", "sources": ["file_id_1", "file_id_2"] }`

### 语义搜索

```bash
curl -s -X POST http://127.0.0.1:8788/search \
  -H "Content-Type: application/json" \
  -d '{"query": "搜索词", "top_k": 10}'
```

### 文件列表

```bash
curl -s http://127.0.0.1:8788/files
```

### 删除文件

```bash
curl -s -X DELETE http://127.0.0.1:8788/file/{file_id}
```

### 健康检查

```bash
curl -s http://127.0.0.1:8788/health
```

## 支持的文件类型

PDF, DOCX, TXT, MD, JSON, CSV

## 注意事项

- 上传大文件可能耗时较长（解析 + 分块 + embedding）
- Chat 使用 Gemini 3.1 Pro（通过 Freestyle 代理）
- Embedding 使用本地 Ollama bge-m3 模型（1024维）
- 数据存储在 SQLite + sqlite-vec 中
