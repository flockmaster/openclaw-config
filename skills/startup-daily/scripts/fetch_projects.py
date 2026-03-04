#!/usr/bin/env python3
"""
每日创业项目抓取脚本
搜索、过滤、整理创业项目，输出 JSON 格式
"""

import json
import sys
from datetime import datetime

def filter_software_projects(projects):
    """过滤掉非软件/互联网相关的项目"""
    keywords_to_exclude = ['养猪', '农业', '种植', '养殖', '农场', '畜牧', '渔业', '农民', '餐饮', '零售']
    
    filtered = []
    for p in projects:
        text = (p.get('title', '') + p.get('desc', '')).lower()
        # 排除关键词
        if any(k in text for k in keywords_to_exclude):
            continue
        filtered.append(p)
    
    return filtered

def main():
    # 示例数据（实际应该用 web_search 动态抓取）
    sample_projects = [
        {
            "source": "Product Hunt",
            "title": "AI Code Review Assistant",
            "desc": "基于 AI 的代码审查工具，自动发现潜在 bug",
            "url": "https://www.producthunt.com/posts/xxx",
            "category": "开发者工具"
        },
        {
            "source": "Indie Hackers",
            "title": "SaaS 月收入从 0 到 1 万美金的复盘",
            "desc": "一个开发者分享他的 SaaS 创业历程",
            "url": "https://www.indiehackers.com/post/xxx",
            "category": "创业故事"
        },
        {
            "source": "36Kr",
            "title": "某 AI 初创完成 A 轮融资",
            "desc": "专注于企业级 AI 应用",
            "url": "https://36kr.com/p/xxx",
            "category": "融资动态"
        },
    ]
    
    # 过滤
    filtered = filter_software_projects(sample_projects)
    
    # 输出 JSON
    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "count": len(filtered),
        "projects": filtered
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
