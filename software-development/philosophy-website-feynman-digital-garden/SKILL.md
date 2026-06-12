---
name: philosophy-website-feynman-digital-garden
description: Build a "philosophy & life-application" interactive website (Next.js) where users pick life problems, match them with philosophers from Russell's History of Western Philosophy, get AI-powered Feynman-style analysis, and conclude with Eastern wisdom shareable cards. Pure AI-driven, no database. Hermes coordinates multi-agent team, Claude Code builds.
category: software-development
triggers:
  - 哲学网站
  - 我在故我在
  - 费曼学习法 网站
  - 哲学 x 生活
  - cogito ergo sum website
---

# Philosophy Website: Feynman x Russell x DeepSeek (Multi-Agent)

Build an interactive philosophy website where users can explore life problems through the lens of philosophers from Bertrand Russell's "A History of Western Philosophy." **No database — all content is AI-generated on the fly.**

## Core Interaction Flow

```
Step 1: 选问题  →  Step 2: 选哲学家  →  Step 3: AI费曼式分析  →  Step 4: 佛道儒结语+分享
```

### Step 1: 选生活问题
- 6大分类：职场困惑、情感关系、消费决策、道德困境、人生意义、科技伦理
- 每类4个预设问题 + 自由输入文本框
- 卡片式布局，点击即选

### Step 2: 选哲学家
- 罗素三卷本标签页切换（古代/中世纪/近代）
- 38位哲学家，按卷筛选 + 流派标签 + 搜索框
- **反差模式开关**：打开后用户故意选不相关的哲学家，制造"驴唇不对马嘴"的思辨张力
- **随缘试试按钮**：随机选一位哲学家

### Step 3: AI分析（费曼学习法）
- 由 DeepSeek V4 Flash 动态生成
- 输出格式：
  - 🧠 一句话说清楚（20字以内）
  - 📖 生活类比（150字以内）
  - 🔬 深度分析（200-300字）
  - 💡 生活建议（50-100字）
  - 🤔 换个角度（用 oppositeIds 中相反哲学家的视角）
- **两套提示词模板**：匹配模式（应用哲学分析）vs 不匹配模式（穿越式创造性对话）
- 打字机效果逐字输出，SSE流式渲染

### Step 4: 佛道儒结语
- 三个大卡片：佛（🕉）/ 道（☯）/ 儒（📚）
- 展示：原文金句 + 出处篇章 + 白话解释
- "分享到朋友圈"（复制文本）和 "保存图片"
- 意境卡片由 CSS 生成（wisdom-quotes.json 的 mood 字段驱动）

## Architecture: Pure AI-Driven (No Database)

```
User → pick question + philosopher
  → POST /api/analyze → DeepSeek V4 Flash (via cc-switch 127.0.0.1:15721)
    → Parse analysis into Feynman format → SSE streaming to user
  → POST /api/wisdom → DeepSeek returns quote + explanation
    → User shares/saves
```

All content is dynamically generated. The only static data:

| File | Content | Purpose |
|------|---------|---------|
| `src/data/philosophers.json` | 38 philosophers, 26 schools, 3 volumes | AI prompt injection context |
| `src/data/wisdom-quotes.json` | 130 quotes (40 Buddhist + 40 Daoist + 50 Confucian) | AI few-shot examples + offline fallback |

## Philosopher Data Schema (38 entries, Russell's framework)

```typescript
interface Philosopher {
  id: string;
  name: string;           // 中文名
  englishName: string;    // 英文名 (not nameEn!)
  volume: 1 | 2 | 3;      // 罗素三卷
  era: string;
  school: string;
  summary: string;         // 50-100字核心思想（用于AI提示词注入）
  keyWorks: string[];      // 主要著作
  oppositeIds: string[];   // 相反哲学家（用于"换个角度"分析，必须双向对称）
  famousQuote: string;
}
```

## Wisdom Quote Schema (130 entries)

```typescript
interface WisdomQuote {
  id: string;
  text: string;            // 原文
  source: string;          // 出处（如《道德经》）
  chapter: string;         // 篇章
  explanation: string;     // 白话解释（20-50字）
  mood: string;            // 意境标签: zen/peaceful/enlightened/wise/compassionate/mysterious
  tags: string[];
}
```

The `mood` field drives CSS意境风格 for the wisdom cards (no external images needed).

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | Next.js 15 (App Router) | SSR首页 + SPA思辨流程 |
| Styling | Tailwind CSS v3 + CSS Variables | warm palette: #1A3A5C / #F5F0EB / #C9A96E |
| Font | Noto Serif SC (Google Fonts) | Chinese philosophy aesthetic |
| AI | DeepSeek V4 Flash | via cc-switch proxy 127.0.0.1:15721 |
| Streaming | SSE (Server-Sent Events) | Typewriter effect rendering |
| Share | Canvas API (pure frontend) | No server-side image generation |
| Deploy | Vercel (Hobby Plan) | Zero cost, auto HTTPS, CDN |

## Multi-Agent Team Structure

| Role | Skill/Agent | Responsibility |
|------|------------|--------------|
| 🏗 **总工程师** | Claude Code | Implementation, architecture decisions |
| 🏛 **前端架构师** | Subagent (delegate_task) | Frontend review, component design, state machine |
| 📋 **监理人** | `project-supervisor` skill | Architecture oversight, philosophy coverage check, design consistency |
| 🔍 **审理人** | `requesting-code-review` skill | Code review, quality gates, PR validation |
| 🎯 **提示词工程师** | `prompt-engineer` skill | 3 prompt templates (analyze/wisdom/concept), GSD meta-prompting methodology |
| 🎨 **设计美学专家** | `frontend-design` (146K⭐) | BOLD aesthetics, typography, motion design |
| 👁 **UI/UX顾问** | `ui-ux-pro-max` (51.2K⭐) | Color palettes (161), font pairings (57), UX guidelines (99) |

## Architecture Decision Process

Use a structured agenda document to coordinate multi-agent decisions:

1. **前端架构师提出问题** (e.g., 5 key questions: Tailwind v3/v4, single/multi philosopher select, URL state vs localStorage)
2. **起草 docs/架构对接议程.md** — categorize decisions into A/B/C/D sections
3. **双方讨论并裁决** — use delegate_task to roleplay both sides
4. **输出 docs/架构决策记录.md** — 23+ decisions with rationale, including data field mismatch corrections

Key decisions discovered in practice:
- Tailwind v3 (not v4) — shadcn/ui compatibility
- URL search params (not localStorage) — shareable state
- MVP single philosopher select (field array reserved for future multi-select)
- CSS mood-driven backgrounds (not AI images) for wisdom cards
- 三层降级: retry → sessionStorage → wisdom-quotes.json random quote (never white screen)

## Feynman Technique Content Model

Each analysis follows strict format:

```
🧠 一句话说清楚：[引用原文，说明对问题的启发，20字以内]
📖 生活类比：[把原文思想类比到用户的生活场景，150字以内]
🔬 原文分析：[直接引用经典原文，逐句解析，关联到用户问题，200-300字]
💡 生活建议：[3条基于该哲学家思想的行动建议]
🤔 换个角度：[oppositeIds相反哲学家视角，可选]
```

### CRITICAL: Every section must LITERALLY QUOTE the user's question

This was the single biggest user complaint. The AI output does reference the question, but doesn't START every section with it. The fix:

**Prompt rule (both client-side mock and DeepSeek API):**
```
铁律：
1. 每一段都必须以"你问{question}"或直接引用用户提问原文开头
2. 每一段正文中必须再多处出现用户提问原文
```

**Mock data factory pattern**: EVERY section starts with the user's question in quotes:
```typescript
oneliner: `你问"${question}"？${philosopher}有言："${quote}"——答案就藏在这句话里。`,
analogy: `想象一下，你问"${question}"的时候，${philosopher}不会直接回答...`,
deep: `你问"${question}"。要理解${philosopher}会如何看待你问的"${question}"，必须回到TA的原文"${quote}"...`,
advice: `针对你问的"${question}"，结合${philosopher}的原文"${quote}"：第一，重读这句话三遍...`,
```

### Loading Animation: KEEP IT SIMPLE (no flickering)

The #1 UX complaint was the loading state "闪来闪去" (flickering) caused by cycling text stages and CSS transitions. 

**Bad** (causes flickering):
```tsx
// Cycling text every 1.2s + opacity transitions = re-render flash
const THINKING_STAGES = ["翻开典籍...", "构建关联...", "提炼洞见..."];
// Don't do this!
```

**Good** (stable, no re-renders):
```tsx
<div style={{ textAlign: "center", padding: "60px 20px" }}>
  <div style={{
    width: 48, height: 48, margin: "0 auto 24px",
    border: "3px solid #EBE5DE", borderTopColor: "var(--accent)",
    borderRadius: "50%", animation: "spin 0.8s linear infinite",
  }} />
  <div style={{ fontSize: 16, color: "var(--text)", marginBottom: 8 }}>
    {philosopher?.name} 正在思考...
  </div>
  <div style={{ fontSize: 13, color: "var(--muted)" }}>
    从哲学的角度审视你的问题
  </div>
</div>
```

Key rules:
- NO cycling text stages (avoids useState updates causing re-renders)
- NO opacity/transition animations on the loading container
- NO ellipsis animation on the text (CSS animations trigger layout)
- Simple static text + CSS-only spinner = zero re-renders

### Sequential Typewriter (fix "闪现" effect)

| Iteration | Problem | Fix |
|-----------|---------|-----|
| v1 | Generic mock data, doesn't reference user's question | Make mock data a **factory function** that takes `question, philosopherName, opposite, famousQuote` params |
| v2 | Content not specific enough to user's actual question | Add iron rule: **every paragraph must literally quote the user's question** with `"${question}"` |
| v3 | Responses don't engage with philosopher's original text | Add `famousQuote` field to all prompts; **every section must reference the philosopher's original quote/works** |

### Fast Mode Prompt (final optimized version)

```
## 任务
用户问了："${question}"
请用${philosopher.name}的思想来回应。必须引用TA的原文进行分析。

## 哲学家档案
姓名：${philosopher.name}
核心思想：${philosopher.summary}
经典名言：${philosopher.famousQuote}

## 铁律
1. 每一段都必须引用该哲学家的原文
2. 用"你"称呼用户，口语化
3. 紧扣"${question}"，不跑题

## 输出结构
【一句话说清楚】引用原文，说明对问题的启发
【生活类比】把原文思想类比到用户的生活场景
【原文分析】直接引用经典原文，逐句解析，关联到用户问题
【行动建议】给用户3条基于该哲学家思想的行动建议
```

### Two prompt templates:
- **匹配模式**: "请用该哲学家的思想体系分析这个问题"
- **不匹配模式**: "用户故意选了一位不相关的哲学家。请先承认这种不匹配，然后发挥想象力——如果这位哲学家穿越到今天，他会如何回应？"

### Mock Data Pattern: Factory Functions (not static objects)

Static mock objects (e.g., `const MOCK_MATCH = {...}`) don't work because they can't reference the user's dynamic input. Always use factory functions:

```typescript
function makeMockMatch(question, philosopherName, philosopherSchool, philosopherEra, philosopherWorks, opposite, famousQuote) {
  return {
    oneliner: `${philosopherName}有言："${famousQuote}"——对"${question}"的回答就藏在这句话里。`,
    analogy: `想象你走到${philosopherName}面前说出"${question}"。TA把名言"${famousQuote}"递给你说：先读懂这句话，再回来看你的问题。`,
    deep: `要理解${philosopherName}会如何看待"${question}"，必须回到TA的原文"${famousQuote}"。这句话表面在讨论${philosopherSchool}，但放到"${question}"面前，你会看到惊人的关联...`,
    advice: `关于"${question}"，结合"${famousQuote}"：第一，重读这句话；第二，问自己如果TA说的对，我该改变什么；第三，做一件小事验证。`,
    alternateView: `如果用${opposite}的视角来看"${question}"...`
  };
}
```

The function signature must match the real `analyzeQuestion` call chain. Every time you add a parameter (like `famousQuote`), update ALL three places:
1. The factory function signature
2. The `analyzeQuestion` wrapper function signature
3. The call site in `think/page.tsx`

### Sequential Typewriter (fix "闪现" effect)

The naive approach — render all sections, animate each with `fadeIn` — causes a **flash** (闪现) because each character update triggers the CSS animation.

**Fix**: Only render sections that are currently typing or already finished. Hide future sections until it's their turn:

```tsx
// For each section key in ["oneliner","analogy","deep","advice","alternateView"]:
const isVisible = isActive || /* section precedes or equals the active section */;
if (!isVisible) return null; // Don't render until it's this section's turn

return (
  <div style={{ opacity: content ? 1 : 0, transition: "opacity 0.15s ease" }}>
    {content}
    {isActive && !done && <span className="cursor-blink" />}
  </div>
);
```

The cursor blink is a simple CSS animation:
```css
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.cursor-blink { display: inline-block; width: 2px; height: 1em; background: var(--primary); animation: blink 0.8s infinite; }
```

### Sequential timing logic:
```typescript
keys.forEach((key, i) => {
  if (i > 0) totalDelay += SECTION_DELAY; // 600ms between sections
  setTimeout(() => setActiveSection(key), totalDelay);
  chars.forEach((char, pos) => {
    setTimeout(() => setTypewriterText(prev => ({
      ...prev, [key]: (prev[key] || "") + char,
    })), totalDelay + pos * TYPING_SPEED); // 28ms per character
  });
  totalDelay += chars.length * TYPING_SPEED;
});
```

## Deployment Architecture

```
Vercel Hobby Plan (zero cost)
├── / (SSR)              → Home page
├── /think (Client SPA)  → 4-step interaction flow (useReducer + Context)
├── /think?... (SSR)     → Share page with OG metadata
├── /concepts (Client)   → Philosopher browsing (38 entries)
├── /api/analyze (Edge)  → DeepSeek proxy + SSE streaming
├── /api/wisdom (Edge)   → Wisdom quote generation
└── Error handling:
    1. Frontend 30s cooldown (localStorage timestamp)
    2. sessionStorage for SSE streaming results
    3. wisdom-quotes.json random quote as ultimate fallback
```

## Known Pitfalls

### JSON files with unescaped ASCII quotes in Chinese text
Subagents generating CJK JSON often use ASCII `"` inside string values instead of Chinese quotation marks `「」` or `""`. This breaks JSON parsing.

**Fix**: Python regex to replace ASCII quotes between CJK characters:
```python
import re
cjk = "[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]"
LQ, RQ = "\u300c", "\u300d"  # corner bracket quotes
while prev != content:
    prev = content
    content = re.sub(
        '(' + cjk + ')"([^"\n]{1,60})"(' + cjk + ')',
        lambda m: m.group(1) + LQ + m.group(2) + RQ + m.group(3),
        content
    )
```

### System python3 broken on Windows
Microsoft Store's `python3` returns exit code 49 with no output. Always use:
```bash
/d/Hermes/portable-hermes-agent/python_embedded/python.exe
```
Check with `which python3` before running scripts.

### Claude Code Orchestration: Three Modes

| Mode | How | When |
|------|-----|------|
| **VS Code Panel** | User pastes task into Claude Code chat in VS Code | Complex multi-file changes, interactive debugging |
| **`claude --print`** | `claude --dangerously-skip-permissions --print "prompt"` | Single-file generation, quick tasks (NOT for pty, NOT background) |
| **Direct file write** | `write_file` / `execute_code` via Hermes | Config files, data files, API routes (most reliable) |

The VS Code panel is a separate process and cannot be controlled programmatically. When the user says "指挥claude干活", they mean writing task descriptions for the user to paste. Don't try to spawn interactive Claude Code sessions — they hang in terminal background mode.

### Chinese characters in execute_code
When writing Python scripts via `execute_code`, Chinese characters in the code cause SyntaxError. Write to a file first with `write_file`, then execute with embedded Python.

### JSON data files must live under src/ for Next.js path aliases
`tsconfig.json` maps `@/*` to `./src/*`. Data files like `philosophers.json` must be at `src/data/`, not `data/`.

### URL State Persistence Pattern
For the 4-step think flow, use a `useThinkUrlState` hook that wraps `useSearchParams`:
```typescript
// src/lib/useUrlState.ts
export function useThinkUrlState() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const state = useMemo(() => ({
    step: searchParams.get("step"),
    question: searchParams.get("question"),
    philosopher: searchParams.get("philosopher"),
    wisdom: searchParams.get("wisdom"),
  }), [searchParams]);

  const updateUrl = useCallback((updates: Partial<ThinkUrlState>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, value]) => {
      value ? params.set(key, value) : params.delete(key);
    });
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [searchParams, router, pathname]);

  return { state, updateUrl, clearUrl };
}
```
This enables shareable URLs like `/think?step=3&question=xxx&philosopher=nietzsche&wisdom=buddhism`.

### SSE API Route Pattern (DeepSeek Proxy)
```typescript
// src/app/api/analyze/route.ts
const PROXY = process.env.DEEPSEEK_PROXY_URL || "http://127.0.0.1:15721/anthropic/v1/messages";

export async function POST(req: NextRequest) {
  const { question, philosopher, isMismatch } = await req.json();
  const deepseekRes = await fetch(PROXY, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": "sk-placeholder" },
    body: JSON.stringify({ model: "deepseek-v4-flash", max_tokens: 2048, stream: true, messages: [...] }),
  });
  const stream = new ReadableStream({...}); // Transform DeepSeek SSE -> our SSE
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
  });
}
```

### Canvas Share Card (Pure Frontend)
Create a `src/components/ShareCard.tsx` component that uses the Canvas API to render a shareable image:
- Three visual styles: buddhism_zen (warm terracotta), daoism_ink (sage green), confucianism_classic (deep brown)
- Draw text with the already-loaded Noto Serif SC font
- `canvas.toBlob()` then `navigator.share()` or download link
- No server-side rendering needed — avoids Vercel Serverless canvas cold starts

### Deployment Configuration
```json
// vercel.json
{
  "framework": "nextjs",
  "regions": ["hkg1"],
  "functions": {
    "src/app/api/analyze/route.ts": { "maxDuration": 30 }
  }
}
```
```bash
# .env.example
DEEPSEEK_PROXY_URL=http://127.0.0.1:15721/anthropic/v1/messages
# For production:
# DEEPSEEK_API_KEY=sk-your-key
# DEEPSEEK_BASE_URL=https://api.deepseek.com/anthropic/v1/messages
```

### Claude Code CLI non-interactive mode
Use `claude --dangerously-skip-permissions --print "prompt"` to execute without interactive session. The `--print` flag outputs to stdout and exits.

### oppositeIds must be bidirectional
If A's oppositeIds includes B, B's oppositeIds must include A. Verify with:
```python
for p in data["philosophers"]:
    for opp in p["oppositeIds"]:
        opp_ph = next((ph for ph in data["philosophers"] if ph["id"] == opp), None)
        assert opp_ph and p["id"] in opp_ph["oppositeIds"]
```

### Architecture documents and actual data files diverge
After generating docs and data files separately, always check field names match reality:
- Field `englishName` not `nameEn`
- Field `buddhism`/`daoism` not `buddhist`/`taoist`
- Philosopher list is flat array (not nested under volumes/parts)
- No `color` field — generate colors from volume ID logic instead
