---
name: xiaohongshu-content-publish
description: Publish图文笔记 to Xiaohongshu (小红书) via Hermes browser automation or Cookie-based API. Two approaches available depending on user preference.
---

# Xiaohongshu Content Publishing

Publish content (图文笔记) to Xiaohongshu through Hermes Agent. Xiaohongshu has no public individual-developer API for content publishing — the Open Platform (`open.xiaohongshu.com`) requires enterprise qualification (营业执照认证). Two practical approaches:

## Approach A: Browser Automation (Recommended)

Hermes navigates to the creator platform, user scans QR code to login, then Hermes fills and publishes.

### What the user needs to prepare:
- **Title**: max 20 chars
- **Body**: plain text, 200-800 chars recommended
- **Images**: JPG/PNG, 3:4 portrait best (1080x1440), 1-9 images
- **Tags**: optional, 2-5 hashtags like `#美食 #AI`
- **Location**: optional, e.g. "上海·新天地"
- **Scheduled time**: optional; if omitted, publish immediately
- **Availability**: user must be at their computer to scan the QR code

### Execution steps:
1. Navigate to `creator.xiaohongshu.com` — the site is a Vue SPA, requires JavaScript
2. The login page shows a QR code — user scans with Xiaohongshu app on phone
3. Use `browser_navigate` → `browser_snapshot` → `browser_type`/`browser_click` to fill the publish form
4. Post-publish: content appears in "内容管理" section

### Pitfalls:
- Cookie session expires after a few hours; user must re-scan each session
- The page is heavily JS-rendered (Vue SPA); `browser_snapshot` may not capture all elements — use `browser_vision` with `annotate=true` for spatial element identification
- Anti-bot measures: avoid rapid clicks, natural typing speed
- Video notes (视频笔记) cannot be published via web — only 图文笔记 is supported on the web platform

## Approach B: Cookie-based API (Fully Automated)

User extracts their session cookie once, Hermes uses it to call Xiaohongshu's internal APIs directly. No manual QR code scanning needed after initial setup.

### What the user needs to prepare:
Same content as Approach A, plus:
- **Cookie string**: extracted from the browser
  1. Open Chrome → navigate to `creator.xiaohongshu.com` and login
  2. F12 → Application → Cookies → `creator.xiaohongshu.com`
  3. Copy the full cookie string (copy all cookies as a single string)
- Cookie typically expires in several hours to ~1 day; needs periodic renewal

### Technical approach:
- Use `terminal` with `curl` to POST to Xiaohongshu's internal publish API endpoints
- Headers must include the session cookie and appropriate User-Agent
- May need to reverse-engineer the API endpoint from the web app's network requests

### Pitfalls:
- Cookie expiration is unpredictable — approach A is more reliable
- Xiaohongshu may rotate API endpoints or add CSRF tokens
- Risk of account being flagged if automated posting is detected (rate limiting recommended)
- This approach is experimental and may break if Xiaohongshu updates their web platform

## Platform Details
- Creator platform URL: `https://creator.xiaohongshu.com/publish/publishNote`
- Open platform (enterprise only): `https://open.xiaohongshu.com/`
- CDN: `fe-static.xhscdn.com`
- Framework: Vue 3 SPA (Element Plus components)
- Image requirements: max 20MB per image, 3:4 ratio recommended
