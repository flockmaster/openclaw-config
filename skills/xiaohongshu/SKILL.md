---
name: xiaohongshu
description: "Download Xiaohongshu (小红书/RedNote) notes. Use when user wants to: (1) get note content (text + images), (2) download note images/videos, (3) get note info (title, author, likes, comments). Supports xhslink.com short links and xiaohongshu.com URLs."
---

# Xiaohongshu Skill

Download notes (text + images/videos) from Xiaohongshu using browser automation.

## Setup (One-Time)

Login to save cookies:

```bash
npx rednote-mcp init
```

Or from source:

```bash
cd /Users/tingjing/.openclaw/skills/xiaohongshu
npm install
npm run init
```

This will open a browser window for you to login. Cookies are saved to `~/.mcp/rednote/cookies.json`.

## Fetch Note Info

```bash
# Get note info (text + image URLs)
python scripts/fetch.py "https://www.xiaohongshu.com/explore/xxx"

# Get note info + download images
python scripts/fetch.py "https://www.xiaohongshu.com/explore/xxx" --download

# Download to specific directory
python scripts/fetch.py "https://xhslink.com/xxx" --download --output ./notes

# Info only (no download)
python scripts/fetch.py "https://xhslink.com/xxx" --info-only
```

## Output

- Text content saved to `.md` file
- Images saved to folder with same name
- JSON metadata saved for programmatic access
