---
name: feynman-philosophy-website-builder
description: Build a philosophy × life application interactive website where users match life problems with philosophers (deliberately or randomly), get AI-powered Feynman-style analysis, and conclude with Eastern wisdom (Buddhism/Daoism/Confucianism) shareable cards. Uses Claude Code as development engine.
---

# Feynman Philosophy × Life Website Builder

Build an interactive philosophy website where ordinary people explore life questions through philosophical thinking, explained in the simplest possible language (Feynman Technique).

## Core Interaction Design

```
Step 1: User selects OR types a life problem (workplace, relationships, ethics, meaning, etc.)
Step 2: User selects a philosopher/school (relevant, irrelevant, or random — "驴唇不对马嘴")
Step 3: AI generates Feynman-style analysis with:
  - One-sentence explanation (like explaining to a child)
  - Everyday life analogy
  - Deeper philosophical analysis
  - Practical life advice
Step 4: User chooses Eastern wisdom conclusion:
  - Buddhism (佛): Zen quote + generated image
  - Daoism (道): Dao De Jing quote + image
  - Confucianism (儒): Analects/Mencius quote + image
Step 5: Share to WeChat Moments or save as image
```

## Tech Stack

- Frontend: Next.js 14+ (App Router) + Tailwind CSS v4 + shadcn/ui
- AI: DeepSeek V4 Flash via cc-switch proxy (127.0.0.1:15721)
- Fonts: Noto Serif SC (Chinese display), Lora (English body)
- Deployment: Vercel / GitHub Pages
- Design references: anthropics/skills/frontend-design (146K stars), nextlevelbuilder/ui-ux-pro-max-skill (51.2K stars)

## Color Palette (Philosophy Site)

- Background: #F5F0EB (warm cream)
- Primary: #1A3A5C (deep blue)
- Accent: #C9A96E (gold)
- Text: #2C1810 (dark brown)
- Muted: #8B7355 (warm gray)

## Feynman Content Template

For every philosophy concept, use this four-part template:

```
🧠 一句话说清楚 (One-liner for a child)
   "就是问自己：如果每个人都这么做，世界会怎样？"

📖 生活类比 (Everyday analogy)
   "就像分蛋糕——切得公平才没人闹"

🔬 深度分析 (Deeper dive — collapsible)
   边沁、密尔的原著核心论点...

💡 生活建议 (Actionable advice)
   "下次在职场遇到道德困境，先问..."
```

## Eastern Wisdom Quote Database

Include curated quotes from:
- **Buddhism**: Heart Sutra, Diamond Sutra, Platform Sutra
- **Daoism**: Dao De Jing, Zhuangzi
- **Confucianism**: Analects, Mencius, Great Learning

Each quote needs: original text, source attribution, plain language explanation, visual style guide for generated image.

## Project Directory Structure

```
project-root/
├── CLAUDE.md              # Project context for Claude Code
├── REQUIREMENTS.md         # Full requirements spec
├── content/
│   ├── concepts/           # Philosophy concept cards (MDX)
│   ├── scenes/             # Life scene definitions
│   └── wisdom/             # Eastern wisdom quotes database
├── components/
│   ├── ProblemSelector/    # Step 1: Life problem selector
│   ├── PhilosopherPicker/  # Step 2: Philosopher/school selector
│   ├── AnalysisCard/       # Step 3: AI analysis results display
│   ├── WisdomConcluder/    # Step 4: Buddha/Dao/Confucius selector
│   └── ShareCard/          # Step 5: Shareable image card
├── lib/
│   ├── ai.ts               # DeepSeek API client with SSE streaming
│   ├── prompts.ts          # Feynman-style prompt templates
│   └── wisdom.ts           # Eastern wisdom quote database
└── docs/
    ├── 技术架构方案.md       # Technical architecture
    ├── 实施计划.md           # Implementation plan
    └── 设计规范.md           # Design specifications
```

## Implementation Phases (16 days)

| Phase | Days | Focus | Key Files |
|-------|------|-------|-----------|
| Phase 1 | 1-2 | Project init + homepage skeleton | Next.js setup, layout, homepage |
| Phase 2 | 3-7 | Core interaction flow (4-step state machine) | ProblemSelector, PhilosopherPicker, AnalysisCard |
| Phase 3 | 8-10 | AI integration + SSE streaming | DeepSeek API client, streaming UI |
| Phase 4 | 11-13 | Wisdom conclusion + share card generation | Canvas API, share to WeChat |
| Phase 5 | 14-16 | Polish animations + Vercel deploy | CSS animations, responsive, CI/CD |

## Installing Design Skills When GitHub Is Blocked

When `git clone` or `npx skills add` times out:

1. Search for the skill content via web search (`ddgs text -k "skills.sh <skill-name>"`)
2. Extract key content from search results (color palettes, font pairings, guidelines)
3. Manually create `~/.claude/skills/<skill-name>/SKILL.md` with condensed content
4. Claude Code will auto-detect the skill from the project directory

## Pitfalls

- **System python3 on Windows may be broken** (exit code 49) — use `D:\Hermes\portable-hermes-agent\python_embedded\python.exe` instead
- **python-docx may not handle Unicode emoji** — avoid `✅` `⚠️` in document generation code, use plain text markers instead
- **GitHub API is often blocked in China** — use ddgs (DuckDuckGo search CLI) as fallback for code/resource discovery
- **cc-switch settings.json may be manually modified** — always check `~/.claude/settings.json` AND `~/.cc-switch/cc-switch.db` to see both the proxy config and the client config
- **Chinese font rendering in matplotlib** — set `plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']` and `axes.unicode_minus = False`
- **Phoenix/Feynman content sections** — keep academic depth behind a "show more" toggle; the default view must be child-level simple
