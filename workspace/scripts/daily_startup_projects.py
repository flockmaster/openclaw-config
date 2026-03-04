#!/usr/bin/env python3
"""
每日创业项目抓取脚本
- 抓取 Product Hunt、Indie Hackers、36Kr 等网站的创业项目
- 过滤掉非软件/互联网相关的项目（如养猪、农业等）
- 输出 JSON 格式，供后续处理
"""

import json
import sys
from datetime import datetime

# 模拟抓取的数据（实际应该用 requests + BeautifulSoup 爬取）
# 这里用示例数据，后续可以扩展真实爬虫

def fetch_product_hunt():
    """Product Hunt - 今日热门产品"""
    # 实际应该调用 Product Hunt API: https://api.producthunt.com/v2/api/graphql
    return [
        {
            "source": "Product Hunt",
            "title": "AI Code Review Assistant",
            "desc": "基于 AI 的代码审查工具，自动发现潜在 bug",
            "url": "https://www.producthunt.com/posts/xxx",
            "category": "开发者工具"
        },
        # 实际应该动态抓取
    ]

def fetch_indie_hackers():
    """Indie Hackers - 独立开发者项目"""
    return [
        {
            "source": "Indie Hackers",
            "title": "SaaS 月收入从 0 到 1 万美金的复盘",
            "desc": "一个开发者分享他的 SaaS 创业历程",
            "url": "https://www.indiehackers.com/post/xxx",
            "category": "创业故事"
        },
    ]

def fetch_36kr():
    """36Kr - 创业资讯"""
    return [
        {
            "source": "36Kr",
            "title": "某 AI 初创完成 A 轮融资",
            "desc": "专注于企业级 AI 应用",
            "url": "https://36kr.com/p/xxx",
            "category": "融资动态"
        },
    ]

def filter_software_projects(projects):
    """过滤掉非软件/互联网相关的项目"""
    keywords_to_exclude = ['养猪', '农业', '种植', '养殖', '农场', '畜牧', '渔业', '农民']
    keywords_to_include = ['软件', 'AI', '互联网', 'SaaS', 'App', '开发者', '技术', '数字', '智能', '平台', '系统']
    
    filtered = []
    for p in projects:
        text = (p.get('title', '') + p.get('desc', '')).lower()
        # 排除关键词
        if any(k in text for k in keywords_to_exclude):
            continue
        # 包含关键词（宽松匹配，没有也保留）
        if any(k in text for k in keywords_to_include):
            filtered.append(p)
        else:
            # 没有关键词也保留，但优先级低
            filtered.append(p)
    
    return filtered

def main():
    all_projects = []
    
    # 抓取各来源
    try:
        all_projects.extend(fetch_product_hunt())
    except Exception as e:
        print(f"Product Hunt 抓取失败：{e}", file=sys.stderr)
    
    try:
        all_projects.extend(fetch_indie_hackers())
    except Exception as e:
        print(f"Indie Hackers 抓取失败：{e}", file=sys.stderr)
    
    try:
        all_projects.extend(fetch_36kr())
    except Exception as e:
        print(f"36Kr 抓取失败：{e}", file=sys.stderr)
    
    # 过滤
    filtered = filter_software_projects(all_projects)
    
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
