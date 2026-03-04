#!/usr/bin/env python3
"""OpenClaw Memory Indexer — 将 markdown 记忆文件索引到 AetherFile 向量库

用法:
  python3 memory_indexer.py index          # 增量索引所有记忆文件
  python3 memory_indexer.py search "查询"  # 语义搜索记忆
  python3 memory_indexer.py status         # 查看索引状态
  python3 memory_indexer.py rebuild        # 强制全量重建
"""

import hashlib
import json
import os
import re
import struct
import sys
import time
from pathlib import Path

import httpx
import sqlite3

# ===== 配置 =====

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", os.path.expanduser("~/.openclaw/workspace")))
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_MD = WORKSPACE / "MEMORY.md"

# AetherFile 数据库（直接操作，不走 HTTP，更快）
AETHERFILE_DB = Path(os.path.expanduser("~/Downloads/aetherfile---ai-桌面归档助手/backend/data/aetherfile.db"))

OLLAMA_URL = "http://127.0.0.1:11434/v1/embeddings"
EMBEDDING_MODEL = "bge-m3"

# 索引状态文件
INDEX_STATE = WORKSPACE / "memory" / ".vector-index-state.json"

# 分块参数
CHUNK_MAX_CHARS = 1200
CHUNK_MIN_CHARS = 100


# ===== Embedding =====

def get_embedding(text: str) -> list[float] | None:
    try:
        resp = httpx.post(
            OLLAMA_URL,
            json={"model": EMBEDDING_MODEL, "input": text[:8000]},
            headers={"Authorization": "Bearer ollama"},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"  Embedding 错误: {e}")
    return None


def serialize_f32(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


# ===== 文本分块 =====

def chunk_markdown(text: str, source_file: str) -> list[dict]:
    """将 markdown 文本按标题和段落分块"""
    chunks = []
    current_heading = ""
    current_content = []
    
    for line in text.split("\n"):
        # 检测标题
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            # 保存之前的内容
            if current_content:
                content = "\n".join(current_content).strip()
                if len(content) >= CHUNK_MIN_CHARS:
                    chunks.append({
                        "heading": current_heading,
                        "content": content,
                        "source_file": source_file,
                    })
            current_heading = heading_match.group(2).strip()
            current_content = []
        else:
            current_content.append(line)
    
    # 最后一块
    if current_content:
        content = "\n".join(current_content).strip()
        if len(content) >= CHUNK_MIN_CHARS:
            chunks.append({
                "heading": current_heading,
                "content": content,
                "source_file": source_file,
            })
    
    # 对过长的块进行切分
    final_chunks = []
    for chunk in chunks:
        content = chunk["content"]
        if len(content) <= CHUNK_MAX_CHARS:
            final_chunks.append(chunk)
        else:
            # 按段落切分
            paragraphs = content.split("\n\n")
            current = []
            current_len = 0
            for para in paragraphs:
                if current_len + len(para) > CHUNK_MAX_CHARS and current:
                    final_chunks.append({
                        "heading": chunk["heading"],
                        "content": "\n\n".join(current),
                        "source_file": chunk["source_file"],
                    })
                    current = [para]
                    current_len = len(para)
                else:
                    current.append(para)
                    current_len += len(para)
            if current:
                final_chunks.append({
                    "heading": chunk["heading"],
                    "content": "\n\n".join(current),
                    "source_file": chunk["source_file"],
                })
    
    # 如果整个文件没有标题，作为一个整体
    if not final_chunks and text.strip():
        final_chunks.append({
            "heading": source_file,
            "content": text.strip()[:CHUNK_MAX_CHARS],
            "source_file": source_file,
        })
    
    return final_chunks


# ===== 索引状态管理 =====

def load_state() -> dict:
    if INDEX_STATE.exists():
        return json.loads(INDEX_STATE.read_text())
    return {"indexed_files": {}}


def save_state(state: dict):
    INDEX_STATE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


# ===== 数据库操作 =====

def get_db():
    import sqlite_vec
    db = sqlite3.connect(str(AETHERFILE_DB), check_same_thread=False)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


def ensure_tables(db):
    """确保向量表存在"""
    db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(embedding float[1024])")
    db.execute("""CREATE TABLE IF NOT EXISTS vec_id_map (
        chunk_id TEXT PRIMARY KEY, rowid_val INTEGER NOT NULL
    )""")
    db.commit()


def delete_memory_file(db, file_id: str):
    """删除一个记忆文件的所有数据"""
    # 删除向量
    rows = db.execute(
        "SELECT chunk_id, rowid_val FROM vec_id_map WHERE chunk_id LIKE ?",
        (f"{file_id}%",)
    ).fetchall()
    for chunk_id, rowid_val in rows:
        db.execute("DELETE FROM chunk_vectors WHERE rowid = ?", (rowid_val,))
        db.execute("DELETE FROM vec_id_map WHERE chunk_id = ?", (chunk_id,))
    
    # 删除 chunks
    db.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
    
    # 删除 file 记录
    db.execute("DELETE FROM files WHERE id = ?", (file_id,))
    db.commit()


def index_memory_file(db, file_path: Path, force: bool = False) -> int:
    """索引一个记忆文件，返回索引的 chunk 数"""
    state = load_state()
    rel_path = str(file_path.relative_to(WORKSPACE))
    current_hash = file_hash(file_path)
    
    # 检查是否需要更新
    if not force and rel_path in state["indexed_files"]:
        if state["indexed_files"][rel_path]["hash"] == current_hash:
            return 0  # 未变更
    
    # 生成 file_id（基于路径的稳定 ID）
    file_id = f"memory-{hashlib.md5(rel_path.encode()).hexdigest()[:16]}"
    
    print(f"  索引: {rel_path}")
    
    # 删除旧数据
    delete_memory_file(db, file_id)
    
    # 读取和分块
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    chunks = chunk_markdown(content, rel_path)
    
    if not chunks:
        print(f"    跳过（无有效内容）")
        return 0
    
    # 插入 file 记录
    db.execute(
        """INSERT OR REPLACE INTO files
           (id, name, type, size, content, category, summary, keywords, embedding, created_at, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_id, rel_path, "md", file_path.stat().st_size, content[:5000],
         "memory", "", "[]", None, int(time.time() * 1000), "openclaw-memory")
    )
    
    # 索引每个 chunk
    indexed = 0
    for i, chunk in enumerate(chunks):
        chunk_id = f"{file_id}-chunk-{i:04d}"
        
        # 组合标题和内容用于 embedding
        embed_text = f"{chunk['heading']}\n{chunk['content']}" if chunk['heading'] else chunk['content']
        embedding = get_embedding(embed_text)
        
        if not embedding:
            print(f"    chunk {i} embedding 失败")
            continue
        
        # 插入 chunk
        db.execute(
            """INSERT OR REPLACE INTO chunks
               (id, file_id, heading, content, embedding, level, parent_id, child_ids, summary, position)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (chunk_id, file_id, chunk["heading"], chunk["content"],
             None, 0, None, "[]", "", i)
        )
        
        # 插入向量
        vec_blob = serialize_f32(embedding)
        cur = db.execute("INSERT INTO chunk_vectors(embedding) VALUES (?)", (vec_blob,))
        db.execute(
            "INSERT OR REPLACE INTO vec_id_map(chunk_id, rowid_val) VALUES (?, ?)",
            (chunk_id, cur.lastrowid)
        )
        indexed += 1
    
    db.commit()
    
    # 更新状态
    state["indexed_files"][rel_path] = {
        "hash": current_hash,
        "file_id": file_id,
        "chunks": indexed,
        "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_state(state)
    
    print(f"    → {indexed} chunks 已索引")
    return indexed


# ===== 搜索 =====

def search_memory(query: str, top_k: int = 5) -> list[dict]:
    """语义搜索记忆"""
    query_emb = get_embedding(query)
    if not query_emb:
        return []
    
    db = get_db()
    ensure_tables(db)
    
    vec_blob = serialize_f32(query_emb)
    
    # 向量搜索，只搜 openclaw-memory 来源的 chunks
    rows = db.execute("""
        SELECT m.chunk_id, v.distance
        FROM chunk_vectors v
        JOIN vec_id_map m ON m.rowid_val = v.rowid
        WHERE v.embedding MATCH ? AND k = ?
        ORDER BY v.distance
    """, (vec_blob, top_k * 3)).fetchall()  # 多取一些再过滤
    
    results = []
    for chunk_id, distance in rows:
        # 只返回记忆来源的
        chunk = db.execute(
            "SELECT c.*, f.source FROM chunks c JOIN files f ON c.file_id = f.id WHERE c.id = ?",
            (chunk_id,)
        ).fetchone()
        
        if chunk and chunk[-1] == "openclaw-memory":  # source 字段
            results.append({
                "chunk_id": chunk_id,
                "file_id": chunk[1],
                "heading": chunk[2],
                "content": chunk[3],
                "distance": distance,
                "score": max(0, 1 - distance),
            })
            if len(results) >= top_k:
                break
    
    db.close()
    return results


# ===== 命令 =====

def cmd_index(force=False):
    """增量索引所有记忆文件"""
    db = get_db()
    ensure_tables(db)
    
    # 收集所有记忆文件
    memory_files = []
    if MEMORY_MD.exists():
        memory_files.append(MEMORY_MD)
    if MEMORY_DIR.exists():
        for f in sorted(MEMORY_DIR.glob("*.md")):
            if not f.name.startswith("."):
                memory_files.append(f)
    
    print(f"发现 {len(memory_files)} 个记忆文件")
    
    total_chunks = 0
    updated = 0
    for f in memory_files:
        n = index_memory_file(db, f, force=force)
        total_chunks += n
        if n > 0:
            updated += 1
    
    db.close()
    print(f"\n完成: {updated} 个文件更新, {total_chunks} 个新 chunks 索引")


def cmd_search(query: str):
    results = search_memory(query)
    if not results:
        print("未找到相关记忆")
        return
    
    print(f"找到 {len(results)} 条相关记忆:\n")
    for r in results:
        score_pct = r["score"] * 100
        print(f"[{score_pct:.0f}%] {r['heading'] or '(无标题)'}")
        print(f"  来源: {r['file_id']}")
        print(f"  内容: {r['content'][:150]}...")
        print()


def cmd_status():
    state = load_state()
    indexed = state.get("indexed_files", {})
    
    if not indexed:
        print("尚未建立索引")
        return
    
    total_chunks = sum(v["chunks"] for v in indexed.values())
    print(f"已索引文件: {len(indexed)}")
    print(f"总 chunks: {total_chunks}")
    print()
    for path, info in sorted(indexed.items()):
        print(f"  {path}: {info['chunks']} chunks (更新于 {info['indexed_at']})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "index":
        cmd_index()
    elif action == "rebuild":
        cmd_index(force=True)
    elif action == "search":
        query = " ".join(sys.argv[2:])
        if not query:
            print("用法: search <查询>")
        else:
            cmd_search(query)
    elif action == "status":
        cmd_status()
    else:
        print(f"未知命令: {action}")
        print(__doc__)
