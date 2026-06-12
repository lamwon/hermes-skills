---
name: philosophy-website-cogito
description: "Complete workflow for building Cogito Ergo Vivo - an interactive philosophy website. Covers: Russell philosopher data (38 thinkers), Buddhist/Daoist/Confucian wisdom (130 quotes), DeepSeek V4 Flash prompt engineering, Next.js+TypeScript full-stack, sequential typewriter effect, Canvas share cards, Vercel deployment. Dual-engine: Hermes Agent plans + Claude Code builds."
category: software-development
---

# Cogito Ergo Vivo — Philosophy Website Complete Workflow

## Project Overview

An interactive website that helps ordinary people understand life problems through philosophical thinking. Users pick a life problem → select a philosopher (deliberately mismatched allowed) → AI generates Feynman-style analysis → choose Buddhism/Daoism/Confucianism for closing wisdom + shareable card.

```
Step 1: Problem  →  Step 2: Philosopher  →  Step 3: Analysis  →  Step 4: Wisdom
(6 categories)     (38 from Russell)      (typewriter + quote)  (Buddha/Dao/Confucian)
(free input)       (3 volumes)            (cite user question)  (share to Moments)
```

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 16 (App Router) + TypeScript |
| Styling | Tailwind CSS v3 + CSS custom properties |
| AI | DeepSeek V4 Flash (cc-switch proxy) |
| Data | JSON files (zero database) |
| Deploy | Vercel (Hobby Plan) |
| Dev | Claude Code (VS Code) + Hermes Agent |

## Team Structure

Product Manager (You) → Hermes Agent (Coordinator) → Claude Code (Chief Engineer) + Frontend Architect (Subagent) + Project Supervisor + Code Reviewer + Prompt Engineer + Design Expert (frontend-design 146K stars) + UI/UX Advisor (ui-ux-pro-max 51.2K stars) + DevOps Engineer

## Data Foundation

### Philosopher Data (38)

Based on Russell's "A History of Western Philosophy" (3 volumes):

- Vol I Ancient: 16 (Thales to Plotinus)
- Vol II Catholic: 4 (Augustine to Ockham)
- Vol III Modern: 18 (Machiavelli to Wittgenstein)

Each philosopher has: id, name, englishName, volume, era, school, summary, keyWorks[], oppositeIds[], famousQuote

### Wisdom Quotes (130)

- Buddhism: 40 (Heart Sutra, Diamond Sutra, Platform Sutra)
- Daoism: 40 (Tao Te Ching, Zhuangzi)
- Confucianism: 50 (Analects, Mencius, Great Learning)

## Core Prompt Rules

1. Every section MUST start with "You asked {question}" or direct quote of user's question
2. Each section body must quote the user's question at least once more
3. Address the user as "you"
4. Stay on-topic
5. Must cite the philosopher's famousQuote in the analysis

## Sequential Typewriter Effect

Sections appear one by one with 600ms gap. Each section types at 28ms/char. Sections not yet reached are NOT rendered (no flash). Blinking cursor on active section.

## GitHub Repository

https://github.com/lamwon/philosophy-website-cogito

## Key Files

| File | Purpose |
|------|---------|
| src/data/philosophers.json | 38 philosopher dataset |
| src/data/wisdom-quotes.json | 130 wisdom quotes |
| src/lib/api.ts | DeepSeek API + mock data |
| src/app/api/analyze/route.ts | SSE streaming API route |
| src/app/think/page.tsx | 4-step interaction page |
| public/test_latest.html | Standalone test (double-click) |

## Installation

```bash
git clone https://github.com/lamwon/philosophy-website-cogito.git
cd philosophy-website-cogito
npm install
npm run dev
```
