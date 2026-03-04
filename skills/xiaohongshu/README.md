# Xiaohongshu Skill

Fetch and download Xiaohongshu (小红书) notes including text content and images.

## Features

- Fetch note content (text + images)
- Download images/videos
- Get note metadata (title, author, likes, comments)
- Support both xhslink.com short links and xiaohongshu.com URLs

## Quick Start

1. **Login (one-time)**:
   ```bash
   npx rednote-mcp init
   ```

2. **Fetch note**:
   ```bash
   python scripts/fetch.py "https://xhslink.com/xxx" --download
   ```

## License

MIT
