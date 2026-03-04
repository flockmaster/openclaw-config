#!/usr/bin/env python3
"""
数学老师 Agent 数据管理层
提供进度、每日记录、错题本、积分的读写接口
"""

import json
import os
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Optional

DATA_DIR = Path(os.environ.get("MATH_TEACHER_DATA", 
    os.path.expanduser("~/.openclaw/workspace-math-teacher/data")))


def _read_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data):
    """原子写入：先写 .tmp 再 mv，旧文件备份为 .bak"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    os.replace(tmp, path)


# ============================================================
# 进度管理
# ============================================================

PROGRESS_FILE = DATA_DIR / "progress.json"

DEFAULT_PROGRESS = {
    "current_unit": 1,
    "current_lesson": 1,
    "units": [],
    "onboarding_completed": False,
    "last_updated": None
}


def get_progress() -> dict:
    return _read_json(PROGRESS_FILE, DEFAULT_PROGRESS.copy())


def update_progress(unit: int, lesson: int):
    p = get_progress()
    p["current_unit"] = unit
    p["current_lesson"] = lesson
    p["last_updated"] = datetime.now().isoformat()
    _write_json(PROGRESS_FILE, p)


def advance_lesson(curriculum: dict):
    """完成一天练习后推进课时"""
    p = get_progress()
    unit_id = p["current_unit"]
    lesson = p["current_lesson"]
    
    # 找当前单元的总课时
    total = None
    for u in curriculum.get("units", []):
        if u["id"] == unit_id:
            total = u["lessons"]
            break
    
    if total and lesson < total:
        update_progress(unit_id, lesson + 1)
    elif total and lesson >= total:
        # 单元完成，进入下一单元
        next_unit = unit_id + 1
        if next_unit <= len(curriculum.get("units", [])):
            update_progress(next_unit, 1)
        # else: 全部学完


def set_onboarding_complete():
    p = get_progress()
    p["onboarding_completed"] = True
    p["last_updated"] = datetime.now().isoformat()
    _write_json(PROGRESS_FILE, p)


# ============================================================
# 每日记录
# ============================================================

DAILY_DIR = DATA_DIR / "daily-records"


def create_daily_record(date_str: str) -> dict:
    record = {
        "date": date_str,
        "source": "daily_practice",
        "questions": [],
        "summary": None,
        "status": "in_progress",
        "started_at": datetime.now().isoformat(),
        "completed_at": None
    }
    path = DAILY_DIR / f"{date_str}.json"
    _write_json(path, record)
    return record


def add_question_result(date_str: str, question: dict):
    path = DAILY_DIR / f"{date_str}.json"
    record = _read_json(path)
    if not record:
        record = create_daily_record(date_str)
    record["questions"].append(question)
    _write_json(path, record)


def complete_daily_record(date_str: str) -> dict:
    path = DAILY_DIR / f"{date_str}.json"
    record = _read_json(path)
    if not record:
        return {}
    
    questions = record.get("questions", [])
    total = len(questions)
    correct = sum(1 for q in questions if q.get("is_correct"))
    
    hint_usage = {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}
    for q in questions:
        level = q.get("hint_level", 0)
        key = f"L{level}"
        if key in hint_usage:
            hint_usage[key] += 1
    
    record["summary"] = {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 2) if total > 0 else 0,
        "points_earned": 0,  # 由积分系统计算后回填
        "hint_usage": hint_usage
    }
    record["status"] = "completed"
    record["completed_at"] = datetime.now().isoformat()
    _write_json(path, record)
    return record


def get_daily_record(date_str: str) -> Optional[dict]:
    path = DAILY_DIR / f"{date_str}.json"
    return _read_json(path) if path.exists() else None


# ============================================================
# 错题本
# ============================================================

MISTAKE_FILE = DATA_DIR / "mistake-book.json"


def _get_mistakes() -> dict:
    return _read_json(MISTAKE_FILE, {"mistakes": []})


def add_mistake(question: dict, error_type: str, prerequisite_missing: str = None):
    data = _get_mistakes()
    mistake_id = f"m-{len(data['mistakes'])+1:03d}"
    data["mistakes"].append({
        "id": mistake_id,
        "question_id": question.get("id"),
        "unit": question.get("unit"),
        "knowledge_point": question.get("knowledge_point"),
        "error_type": error_type,
        "prerequisite_missing": prerequisite_missing,
        "original_question": question.get("content"),
        "correct_answer": question.get("correct_answer"),
        "student_answer": question.get("student_answer"),
        "first_wrong_date": date.today().isoformat(),
        "review_count": 0,
        "consecutive_correct": 0,
        "mastered": False,
        "last_reviewed": None
    })
    _write_json(MISTAKE_FILE, data)
    return mistake_id


def get_review_candidates(count: int = 1) -> list:
    """获取待复习错题（未掌握，优先最久没复习的）"""
    data = _get_mistakes()
    candidates = [m for m in data["mistakes"] if not m["mastered"]]
    candidates.sort(key=lambda m: m.get("last_reviewed") or "0000")
    return candidates[:count]


def mark_review_result(mistake_id: str, correct: bool):
    data = _get_mistakes()
    for m in data["mistakes"]:
        if m["id"] == mistake_id:
            m["review_count"] += 1
            m["last_reviewed"] = date.today().isoformat()
            if correct:
                m["consecutive_correct"] += 1
                if m["consecutive_correct"] >= 2:
                    m["mastered"] = True
            else:
                m["consecutive_correct"] = 0
            break
    _write_json(MISTAKE_FILE, data)


# ============================================================
# 积分系统
# ============================================================

POINTS_FILE = DATA_DIR / "points.json"

DEFAULT_POINTS = {
    "total_points": 0,
    "consecutive_days": 0,
    "max_consecutive_days": 0,
    "last_practice_date": None,
    "achievements": [],
    "history": []
}


def get_points() -> dict:
    return _read_json(POINTS_FILE, DEFAULT_POINTS.copy())


def add_points(amount: int, event: str) -> int:
    """增加积分，返回新总分。只增不减。"""
    if amount <= 0:
        return get_points()["total_points"]
    
    data = get_points()
    data["total_points"] += amount
    
    today = date.today().isoformat()
    # 更新今日历史
    today_entry = None
    for h in data["history"]:
        if h["date"] == today:
            today_entry = h
            break
    if today_entry:
        today_entry["earned"] += amount
        today_entry["events"].append(event)
    else:
        data["history"].append({
            "date": today,
            "earned": amount,
            "events": [event]
        })
    
    _write_json(POINTS_FILE, data)
    return data["total_points"]


def check_and_update_consecutive_days() -> int:
    """检查并更新连续天数，返回当前连续天数"""
    data = get_points()
    today = date.today().isoformat()
    yesterday = (date.today().replace(day=date.today().day - 1)).isoformat() if date.today().day > 1 else None
    
    if data["last_practice_date"] == today:
        return data["consecutive_days"]
    
    if data["last_practice_date"] == yesterday:
        data["consecutive_days"] += 1
    else:
        data["consecutive_days"] = 1
    
    data["last_practice_date"] = today
    if data["consecutive_days"] > data["max_consecutive_days"]:
        data["max_consecutive_days"] = data["consecutive_days"]
    
    _write_json(POINTS_FILE, data)
    return data["consecutive_days"]


def check_achievement(achievement_id: str) -> bool:
    data = get_points()
    return any(a["id"] == achievement_id for a in data["achievements"])


def grant_achievement(achievement_id: str, name: str, points: int):
    if check_achievement(achievement_id):
        return  # 已获得
    data = get_points()
    data["achievements"].append({
        "id": achievement_id,
        "name": name,
        "earned_at": date.today().isoformat(),
        "points": points
    })
    data["total_points"] += points
    _write_json(POINTS_FILE, data)


# ============================================================
# CLI 入口（供 skill 脚本调用）
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: data_manager.py <command> [args...]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "get_progress":
        print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
    elif cmd == "get_points":
        print(json.dumps(get_points(), ensure_ascii=False, indent=2))
    elif cmd == "get_review_candidates":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        print(json.dumps(get_review_candidates(count), ensure_ascii=False, indent=2))
    elif cmd == "get_daily_record":
        date_str = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
        r = get_daily_record(date_str)
        print(json.dumps(r, ensure_ascii=False, indent=2) if r else "null")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
