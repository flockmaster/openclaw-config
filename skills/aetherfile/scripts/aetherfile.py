#!/usr/bin/env python3
"""AetherFile 意图检测 + API 调用工具

用法:
  python3 aetherfile.py detect "用户消息"     → 判断是否需要 AetherFile
  python3 aetherfile.py chat "问题"            → RAG 问答
  python3 aetherfile.py search "关键词"        → 语义搜索
  python3 aetherfile.py files                  → 文件列表
  python3 aetherfile.py upload /path/to/file   → 上传文件
  python3 aetherfile.py delete <file_id>       → 删除文件
  python3 aetherfile.py health                 → 健康检查
"""

import json
import re
import subprocess
import sys

BASE_URL = "http://127.0.0.1:8788"

# ===== 意图检测 =====

FILE_KEYWORDS = [
    "文件", "文档", "资料", "PDF", "pdf", "DOCX", "docx",
    "归档", "上传", "下载", "删除文件",
    "知识库", "搜索文档", "查找文档", "搜索文件",
    "总结文档", "摘要", "文档说", "文件里",
    "报告", "手册", "需求说明", "会议纪要",
]

FILE_PATTERNS = [
    r"帮我找.*(文件|文档|资料|纪要|报告|手册)",
    r"搜索.*关于",
    r"总结.*(这个|文档|文件)",
    r"文档里.*怎么说",
    r"根据.*(文档|文件)",
    r".*在哪个文件",
    r"上传.*文件",
    r"删除.*文件",
    r"文件列表",
    r"知识库",
    r"北汽.*APP",  # 项目特定关键词
    r"(查|找|搜).*(之前|上次).*(的|了)",
    r".*(文件|文档).*(有哪些|列表|多少)",
]

def detect_intent(message: str) -> dict:
    """检测消息是否与文件操作相关"""
    message_lower = message.lower()
    
    # 关键词匹配
    keyword_hits = [kw for kw in FILE_KEYWORDS if kw.lower() in message_lower]
    
    # 正则匹配
    pattern_hits = [p for p in FILE_PATTERNS if re.search(p, message)]
    
    # 计算置信度
    confidence = 0.0
    if keyword_hits:
        confidence += min(len(keyword_hits) * 0.2, 0.6)
    if pattern_hits:
        confidence += min(len(pattern_hits) * 0.3, 0.6)
    confidence = min(confidence, 1.0)
    
    # 判断动作类型
    action = "chat"  # 默认 RAG 问答
    if re.search(r"上传|归档|存起来", message):
        action = "upload"
    elif re.search(r"搜索|查找|找.*文件", message):
        action = "search"
    elif re.search(r"文件列表|列出.*文件|有哪些文件", message):
        action = "files"
    elif re.search(r"删除.*文件", message):
        action = "delete"
    
    return {
        "is_file_intent": confidence >= 0.3,
        "confidence": round(confidence, 2),
        "action": action,
        "keyword_hits": keyword_hits,
        "pattern_hits": pattern_hits,
    }


# ===== API 调用 =====

def curl(method, path, data=None, file_path=None):
    """调用 AetherFile API"""
    url = f"{BASE_URL}{path}"
    cmd = ["curl", "-s"]
    
    if method == "POST" and file_path:
        cmd += ["-X", "POST", "-F", f"file=@{file_path}", url]
    elif method == "POST" and data:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(data), url]
    elif method == "DELETE":
        cmd += ["-X", "DELETE", url]
    else:
        cmd += [url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return json.loads(result.stdout) if result.stdout.strip() else {"error": "empty response"}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except json.JSONDecodeError:
        return {"error": "invalid json", "raw": result.stdout[:500]}


def cmd_detect(message):
    result = detect_intent(message)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_chat(query):
    result = curl("POST", "/chat", {"query": query})
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_search(query, top_k=10):
    result = curl("POST", "/search", {"query": query, "top_k": top_k})
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_files():
    result = curl("GET", "/files")
    if isinstance(result, list):
        for f in result:
            size_kb = f.get("size", 0) // 1024
            print(f"  [{f['id'][:8]}] {f['name']} ({f['type']}, {size_kb}KB)")
    else:
        print(json.dumps(result, ensure_ascii=False))

def cmd_upload(file_path):
    result = curl("POST", "/upload", file_path=file_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_delete(file_id):
    result = curl("DELETE", f"/file/{file_id}")
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_health():
    result = curl("GET", "/health")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        "detect": lambda: cmd_detect(" ".join(args)),
        "chat": lambda: cmd_chat(" ".join(args)),
        "search": lambda: cmd_search(" ".join(args)),
        "files": cmd_files,
        "upload": lambda: cmd_upload(args[0]) if args else print("用法: upload <path>"),
        "delete": lambda: cmd_delete(args[0]) if args else print("用法: delete <file_id>"),
        "health": cmd_health,
    }
    
    if action in commands:
        commands[action]()
    else:
        print(f"未知命令: {action}")
        print(__doc__)
