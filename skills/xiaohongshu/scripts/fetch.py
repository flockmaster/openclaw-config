#!/usr/bin/env python3
"""
Fetch Xiaohongshu (小红书) note content and download images.

Usage:
    python fetch.py <url> [--download] [--output <dir>] [--info-only]

Examples:
    python fetch.py "https://www.xiaohongshu.com/explore/xxx"
    python fetch.py "https://xhslink.com/xxx" --download
    python fetch.py "https://xhslink.com/xxx" --info-only
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Cookie storage path (same as rednote-mcp)
COOKIE_FILE = Path.home() / ".mcp" / "rednote" / "cookies.json"


class XiaohongshuFetcher:
    def __init__(self):
        self.browser = None
        self.page = None
        self.cookies = []
    
    async def setup(self):
        """Initialize browser and load cookies."""
        from playwright.async_api import async_playwright
        
        # Load cookies
        if COOKIE_FILE.exists():
            with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                self.cookies = json.load(f)
            logger.info(f"Loaded {len(self.cookies)} cookies from {COOKIE_FILE}")
        else:
            logger.warning(f"No cookies found at {COOKIE_FILE}. Please run: npx rednote-mcp init")
            raise RuntimeError("Please login first: npx rednote-mcp init")
        
        # Start browser
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Create context with cookies
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Add cookies
        if self.cookies:
            await context.add_cookies(self.cookies)
        
        self.page = await context.new_page()
        
        # Verify login
        await self.page.goto('https://www.xiaohongshu.com', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)
        
        # Check if logged in
        is_logged_in = await self.page.evaluate('''() => {
            const userElem = document.querySelector('.user.side-bar-component .channel');
            return userElem && userElem.textContent.trim() === '我';
        }''')
        
        if not is_logged_in:
            raise RuntimeError("Not logged in. Please run: npx rednote-mcp init")
        
        logger.info("Login verified")
    
    async def close(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    
    def extract_note_id(self, url: str) -> str:
        """Extract note ID from URL."""
        # Handle xhslink.com short URLs
        if 'xhslink.com' in url:
            # Need to resolve short URL
            return url
        
        # Handle xiaohongshu.com URLs
        patterns = [
            r'/explore/([a-zA-Z0-9]+)',
            r'/discovery/item/([a-zA-Z0-9]+)',
            r'noteId=([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return url
    
    async def resolve_short_url(self, url: str) -> str:
        """Resolve xhslink.com short URL to full URL."""
        if 'xhslink.com' not in url:
            return url
        
        try:
            # Use requests to follow redirect
            response = requests.get(url, allow_redirects=True, timeout=10,
                                  headers={'User-Agent': 'Mozilla/5.0'})
            return response.url
        except Exception as e:
            logger.warning(f"Failed to resolve short URL: {e}")
            return url
    
    async def fetch_note(self, url: str) -> Dict[str, Any]:
        """Fetch note content and metadata."""
        # Resolve short URL
        full_url = await self.resolve_short_url(url)
        logger.info(f"Fetching: {full_url}")
        
        # Navigate to note page
        await self.page.goto(full_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)  # Wait for content to load
        
        # Scroll to load more content
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        
        # Extract note data
        note_data = await self.page.evaluate('''() => {
            // Try to find note data in page
            const result = {
                title: '',
                content: '',
                author: { name: '', id: '', avatar: '' },
                images: [],
                video: null,
                likes: 0,
                collects: 0,
                comments: 0,
                shares: 0,
                time: '',
                note_id: ''
            };
            
            // Title
            const titleElem = document.querySelector('.title span');
            if (titleElem) result.title = titleElem.textContent.trim();
            
            // Content
            const contentElem = document.querySelector('.desc .content');
            if (contentElem) result.content = contentElem.textContent.trim();
            
            // Author
            const authorElem = document.querySelector('.author .name');
            if (authorElem) result.author.name = authorElem.textContent.trim();
            const avatarElem = document.querySelector('.author .avatar img');
            if (avatarElem) result.author.avatar = avatarElem.src;
            
            // Images
            const imageElems = document.querySelectorAll('.album-item img');
            imageElems.forEach(img => {
                if (img.src && !result.images.includes(img.src)) {
                    result.images.push(img.src);
                }
            });
            
            // Video
            const videoElem = document.querySelector('video');
            if (videoElem) result.video = videoElem.src || videoElem.currentSrc;
            
            // Stats
            const likeElem = document.querySelector('[data-type="like"] .count');
            if (likeElem) result.likes = parseInt(likeElem.textContent) || 0;
            
            const collectElem = document.querySelector('[data-type="collect"] .count');
            if (collectElem) result.collects = parseInt(collectElem.textContent) || 0;
            
            const commentElem = document.querySelector('[data-type="comment"] .count');
            if (commentElem) result.comments = parseInt(commentElem.textContent) || 0;
            
            // Time
            const timeElem = document.querySelector('.time');
            if (timeElem) result.time = timeElem.textContent.trim();
            
            // Note ID from URL
            const urlParts = window.location.pathname.split('/');
            result.note_id = urlParts[urlParts.length - 1] || '';
            
            return result;
        }''')
        
        # If basic extraction failed, try to find embedded JSON
        if not note_data['title'] and not note_data['content']:
            note_data = await self.extract_embedded_data()
        
        return note_data
    
    async def extract_embedded_data(self) -> Dict[str, Any]:
        """Try to extract data from embedded JSON in page."""
        result = {
            'title': '', 'content': '', 'author': {'name': '', 'id': '', 'avatar': ''},
            'images': [], 'video': None, 'likes': 0, 'collects': 0, 'comments': 0,
            'shares': 0, 'time': '', 'note_id': ''
        }
        
        # Get page source and search for JSON
        page_source = await self.page.content()
        
        # Look for common patterns
        patterns = [
            r'"noteData":\s*({[^}]+})',
            r'"note":\s*({[^}]+})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_source)
            if match:
                try:
                    data = json.loads(match.group(1))
                    result.update(data)
                    break
                except:
                    pass
        
        return result
    
    def download_image(self, url: str, output_path: Path) -> Path:
        """Download image from URL."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.xiaohongshu.com/',
        }
        
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return output_path
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None


def save_note(note: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    """Save note content to files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    note_id = note.get('note_id', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"{note_id}_{timestamp}"
    
    # Save metadata as JSON
    json_path = output_dir / f"{base_name}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(note, f, ensure_ascii=False, indent=2)
    
    # Save text content as Markdown
    md_path = output_dir / f"{base_name}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {note.get('title', 'Untitled')}\n\n")
        f.write(f"**作者**: {note.get('author', {}).get('name', 'Unknown')}\n")
        f.write(f"**时间**: {note.get('time', 'Unknown')}\n")
        f.write(f"**点赞**: {note.get('likes', 0):,} | **收藏**: {note.get('collects', 0):,} | **评论**: {note.get('comments', 0):,}\n\n")
        f.write(f"---\n\n")
        f.write(f"{note.get('content', 'No content')}\n")
        if note.get('images'):
            f.write(f"\n---\n\n## 图片 ({len(note['images'])})\n")
            for i, img in enumerate(note['images'], 1):
                f.write(f"![Image {i}]({img})\n")
    
    return {
        'json': json_path,
        'markdown': md_path,
        'images': []
    }


def download_images(note: Dict[str, Any], output_dir: Path, fetcher: XiaohongshuFetcher) -> List[Path]:
    """Download all images from note."""
    images_dir = output_dir / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    
    for i, img_url in enumerate(note.get('images', []), 1):
        ext = Path(img_url.split('?')[0]).suffix or '.jpg'
        img_path = images_dir / f"image_{i:03d}{ext}"
        
        logger.info(f"Downloading image {i}/{len(note['images'])}")
        result = fetcher.download_image(img_url, img_path)
        if result:
            downloaded.append(result)
    
    return downloaded


async def main_async(args):
    """Main async function."""
    fetcher = XiaohongshuFetcher()
    
    try:
        await fetcher.setup()
        note = await fetcher.fetch_note(args.url)
        
        # Display info
        print(f"\n{'='*60}")
        print(f"标题：{note.get('title', 'N/A')}")
        print(f"作者：{note.get('author', {}).get('name', 'N/A')}")
        print(f"时间：{note.get('time', 'N/A')}")
        print(f"点赞：{note.get('likes', 0):,} | 收藏：{note.get('collects', 0):,} | 评论：{note.get('comments', 0):,}")
        print(f"{'='*60}")
        
        if note.get('content'):
            content = note['content']
            if len(content) > 200:
                content = content[:200] + '...'
            print(f"\n内容:\n{content}\n")
        
        if note.get('images'):
            print(f"图片：{len(note['images'])} 张")
        
        if args.info_only:
            if note.get('images'):
                print(f"\n图片 URLs:")
                for i, img in enumerate(note['images'], 1):
                    print(f"  {i}. {img}")
            return
        
        # Save and download
        output_dir = Path(args.output) if args.output else Path(__file__).parent.parent / 'data' / 'notes'
        
        if args.download:
            print(f"\n保存笔记...")
            saved = save_note(note, output_dir)
            print(f"元数据：{saved['json']}")
            print(f"正文：{saved['markdown']}")
            
            if note.get('images'):
                print(f"\n下载图片...")
                images = download_images(note, output_dir, fetcher)
                print(f"已下载 {len(images)} 张图片到：{output_dir / 'images'}")
        else:
            print(f"\n使用 --download 保存笔记和图片")
            print(f"使用 --output <目录> 指定保存路径")
    
    finally:
        await fetcher.close()


def main():
    parser = argparse.ArgumentParser(description='Fetch Xiaohongshu note content')
    parser.add_argument('url', help='Note URL (xhslink.com or xiaohongshu.com)')
    parser.add_argument('--download', '-d', action='store_true', help='Download images and save content')
    parser.add_argument('--output', '-o', help='Output directory', default=None)
    parser.add_argument('--info-only', '-i', action='store_true', help='Only show info, no download')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        asyncio.run(main_async(args))
    except Exception as e:
        print(f"\n错误：{e}", file=sys.stderr)
        if 'login' in str(e).lower() or 'cookie' in str(e).lower():
            print("\n请先登录：npx rednote-mcp init", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
