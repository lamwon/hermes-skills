---
name: github-repo-star-boost
description: Polish a GitHub repository to attract stars — generate real example images via free APIs, write bilingual README with badges/comparison tables/FAQ, and create platform-specific share posts for Chinese and English social media.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [github, stars, promotion, readme, social-media]
---

# GitHub Repo Star Boost — README Polish + Promotion

Systematic workflow to improve a GitHub repo's attractiveness and create shareable promotional content across platforms.

## When to Use

- User asks you to "make my repo look better" or "get more stars"
- Repo has 0-50 stars, basic README, no example images
- User wants to publish/share their repo on social media
- Chinese+English bilingual audience (optimized for users in China)

## Prerequisites

- Local git clone of the repo with push access
- GitHub token or cached git credentials
- A free image generation API for sample images (see below)
- DeepSeek API or other LLM for generating prompts/content

## Step 1: Assess Current State

```bash
# Check repo files
curl -s "https://api.github.com/repos/{owner}/{repo}/contents/" | python -c "import sys,json; d=json.load(sys.stdin); [print(x['name'], x['type']) for x in d]"

# Read current README
curl -s "https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"

# Check star count
curl -s "https://api.github.com/repos/{owner}/{repo}" | python -c "import sys,json; d=json.load(sys.stdin); print('Stars:', d['stargazers_count'])"
```

## Step 2: Generate Example Images (Free, No Key Needed)

Use **Pollinations.ai** — a completely free image generation API. No API key required. Best prompts are short and descriptive.

```bash
# Simple prompt — works reliably
curl -s -o examples/sample1.jpg \
  "https://image.pollinations.ai/prompt/cyberpunk%20cat%20neon%20lights%20rainy%20alley?width=512&height=512&nologo=true"

# For better prompt quality, use DeepSeek V4 to craft prompts first
curl -s https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"Generate 4 short FLUX image prompts: ... Return JSON array."}],"max_tokens":500}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"
```

**Known issues from China:**
- Pollinations.ai is accessible but SLOW (10-45 seconds per image)
- Use `--max-time 45` on each curl call
- Download images one at a time (not in parallel) to avoid timeout
- For Chinese users, a fallback is to use SiliconFlow API if they have a key

**Verify images are valid JPEGs:**
```bash
file examples/*.jpg
# Expected: "JPEG image data, ... 512x512, components 3"
# NOT: "JSON text data" (means error — retry)
```

## Step 3: Write a Killer README

Structure for a star-attracting README:

```
# 🎯 Project Title (Chinese + English)

<p align="center">
  [Example images — 2x2 grid showing best outputs]
</p>

<p align="center">
  [Badges: license, language version, integrations, key technologies]
</p>

---

## 📖 简介 | Introduction

[1-2 paragraphs explaining what it does and why it matters]

### ✨ 核心亮点 | Highlights

| Feature | Description |
|---------|-------------|
| 🆓 Zero cost | ... |
| 🚀 One command | ... |
| 🇨🇳 China-friendly | ... |

---

## 🖼️ 效果预览 | Examples

| Style | Prompt | Preview |
|-------|--------|---------|
| Cyberpunk | "..." | ![][img1] |
| Ink painting | "..." | ![][img2] |

[Define image references at bottom of file]

---

## 🚀 快速开始 | Quick Start

[Step-by-step with code blocks]

---

## 🔄 与主流方案对比 | Comparison

| Solution | Cost | Quality | Speed | China | GPU needed? |
|----------|------|---------|-------|-------|-------------|
| **This** | ✅ Free | ⭐⭐⭐⭐ | ⚡ Fast | ✅ | ❌ |
| Competitor A | 💰 $10/mo | ⭐⭐⭐⭐⭐ | ⚡ Fast | ❌ | ❌ |

---

## ❓ FAQ

[2-5 common questions]

---

## 📣 Share

[Platform links]

---

## 📄 License

MIT
```

**Key README elements that attract stars:**
1. **Example images at the top** — showing real output is the #1 draw
2. **Badges** — visual credibility (shields.io badges)
3. **Comparison table** — helps users understand why they should use this
4. **Chinese + English** — reaches both markets (critical for China-based repos)
5. **Quick start in 3 steps** — reduce friction to try

## Step 4: Create SHARE_POSTS.md

Create a file with ready-to-publish posts for multiple platforms. Each platform needs a different tone:

| Platform | Tone | Language | Style |
|----------|------|----------|-------|
| **知乎** | Long-form tutorial, tech deep-dive | Chinese | "发现了一个..." problem-solution |
| **V2EX** | Community share, technical | Chinese | Direct, "分享一个..." |
| **小红书** | Casual, emoji-heavy, "种草" | Chinese | "家人们谁懂啊！" + tags |
| **即刻** | Short, image-focused | Chinese | Casual observation |
| **Twitter/X** | Thread-style, English | English | Short 🧵 |
| **Reddit** | Subreddit-appropriate | English | Technical, with link |

## Step 5: Push to GitHub

```bash
git add README.md SHARE_POSTS.md examples/
git commit -m "Polish: new README, example images, share posts"
git push
```

## Step 5b (Optional): Create Share Card Images with PIL

Generate programmatic social media card images using Python PIL (works on Windows with system Chinese fonts):

```python
from PIL import Image, ImageDraw, ImageFont

output_dir = "examples"
W, H = 1200, 630  # GitHub social preview size
img = Image.new("RGB", (W, H), (15, 23, 42))
draw = ImageDraw.Draw(img)

# Use Microsoft YaHei for Chinese text (Windows)
font_path = "C:\\Windows\\Fonts\\msyh.ttc"
title_font = ImageFont.truetype(font_path, 52)
body_font = ImageFont.truetype(font_path, 30)
small_font = ImageFont.truetype(font_path, 22)

# Draw title
draw.text((x, y), "Title Text", fill=(0, 200, 255), font=title_font)

# Rounded rectangle "badge" backgrounds
draw.rounded_rectangle([(x, y), (x+w, y+36)], radius=18, outline=color, width=2)

img.save(os.path.join(output_dir, "social-preview.png"))
```

**Recommended sizes:**
| Platform | Size | Notes |
|----------|------|-------|
| GitHub Social Preview | 1200x630 | Auto-detected from repo |
| 小红书 / 朋友圈 | 1080x1080 | Square card |
| 竖版长图 | 1080x1920 | For timeline posts |

**Chinese font fallback order on Windows:**
1. `C:\\Windows\\Fonts\\msyh.ttc` (Microsoft YaHei — best for most use cases)
2. `C:\\Windows\\Fonts\\msyhbd.ttc` (YaHei Bold)
3. `C:\\Windows\\Fonts\\simhei.ttf` (SimHei — good fallback)
4. `C:\\Windows\\Fonts\\arial.ttf` (English-only fallback)

## Step 6: Set GitHub Repo Metadata via API

Extract the token from the git remote URL, then update topics and description:

```python
import subprocess, json, urllib.request

# Extract token from git remote URL
result = subprocess.run(
    ["git", "remote", "get-url", "origin"],
    capture_output=True, text=True, cwd="/path/to/repo"
)
url = result.stdout.strip()
# URL format: https://username:ghp_token@github.com/owner/repo.git
token = url.split(":")[-1].split("@")[0]

# Set topics
req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/topics",
    data=json.dumps({"names": ["tag1", "tag2", ...]}).encode(),
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.mercy-preview+json",
    },
    method="PUT"
)
urllib.request.urlopen(req)

# Update repo description
req2 = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}",
    data=json.dumps({"description": "New description"}).encode("utf-8"),
    headers={
        "Authorization": f"token {token}",
        "Content-Type": "application/json; charset=utf-8",
    },
    method="PATCH"
)
urllib.request.urlopen(req2)
```

## Step 7: Open Browser Pages for the User

On Windows, use `start` command to open browser tabs:

```bash
start https://github.com/owner/repo
start https://v2ex.com/go/create
start https://zhihu.com/write
start https://www.xiaohongshu.com/explore
```

Note: This opens the user's default browser. The assistant cannot actually post — the user must click submit.

## Pitfalls

- **Pollinations.ai from China is SLOW** — expect 15-45s per image. Download one at a time with `--max-time 45`. If it times out, the file may be partial or JSON error text — always `file`-check the result.
- **Verify downloaded images** — Use `file examples/*.jpg`. Expected: `JPEG image data, ... 512x512, components 3`. If output is `JSON text data`, the API returned an error — re-download.
- **Git on Windows (Git Bash)** — Use `/d/` style paths (`/d/Hermes/repo`), NOT `D:\` or `/d/D:`
- **Redacting keys** — the .env file values are masked in tool outputs. Use `grep` + `cut` in terminal to extract them: `grep API_KEY ~/.hermes/.env | cut -d= -f2-`
- **Chinese social media platforms** — V2EX, 知乎, 小红书, 即刻 all require user accounts to post. The assistant can prepare the text but cannot post on the user's behalf.
- **README image paths** — Use relative paths like `examples/image.jpg`, not absolute URLs, so images display in both GitHub web and local clone.
- **Big images slow down README loading** — Use 512x512, not full resolution.
