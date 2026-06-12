---
name: hermes-project-orchestrator
description: Use Hermes Agent as a project orchestrator — survey local knowledge assets (WorkBuddy, Obsidian, IMA skills), search external resources (GitHub, web), create structured build plans, then delegate execution to Claude Code. Hermes handles planning/coordination, Claude Code handles implementation.
category: software-development
---

# Hermes Project Orchestrator

Use when the user wants to build something (website, tool, system) that combines:
- Their existing local knowledge/work content (WorkBuddy results, Obsidian notes, IMA Skills)
- External open-source resources from GitHub
- AI-assisted development (Claude Code)

## Workflow

### Phase 1: Asset Survey

Survey all local knowledge bases systematically:

```bash
# 1. WorkBuddy — find actual location (may be NTFS-junctioned to D:)
ls -la /c/Users/Windows/WorkBuddy/
# or
ls -la /d/WorkBuddy/

# Look for philosophy/research paper directories
find /c/Users/Windows/WorkBuddy/ -maxdepth 2 -name "*.docx" -o -name "*.md" | head -30

# 2. Obsidian vault
ls /d/my-knowledge-base/wiki/

# 3. IMA skills (may be at desktop/workbuddy)
ls /d/HuaweiMoveData/Users/Windows/Desktop/workbuddy/ima-skills/

# 4. Check Hermes built-in skills
skills_list()
skill_view("concept-to-application-analysis")  # Key skill for philosophy->life mapping
```

### Phase 2: External Resource Search

GitHub may be blocked in China. Use ddgs CLI (DuckDuckGo search) instead:

```bash
# Search GitHub repos via web
ddgs text -k "philosophy applied ethics github repository" -m 5

# Search for specific topic repos
ddgs text -k "awesome-philosophy site:github.com" -m 5

# For Claude Code skills
ddgs text -k "awesome-claude-skills github" -m 3
```

Key repositories to look for:
- awesome-philosophy / awesome-ethics (curated resource lists)
- awesome-claude-skills (Claude Code skills collection)
- digital-gardeners (Digital Garden methodology)
- Next.js/Tailwind content site templates

### Phase 3: Create Structured Plan Document

Use python-docx with Hermes embedded Python (NOT system python3 which may be broken):

```bash
# ALWAYS use Hermes embedded Python for python-docx:
/d/Hermes/portable-hermes-agent/python_embedded/python.exe -c "from docx import Document; print('ok')"
```

Document structure template:
1. Title page with project name + subtitle
2. Table of Contents
3. Project Overview (定位、使命、目标受众)
4. Core Content System (三层架构: 理论根基→应用领域→生活实践)
5. Knowledge Base Inventory (WorkBuddy + Obsidian + Hermes Skills)
6. External Resource Integration Plan (GitHub repos to clone/adapt)
7. Technical Architecture (tech stack + site map + content format)
8. Feature Design (core + stretch features)
9. Implementation Roadmap (phased with Claude Code)
10. Risk Assessment

### Phase 4: Delegate to Claude Code

Once the plan is approved, execution happens via Claude Code:
- Hermes Agent handles: planning, coordination, quality review, cronjob scheduling
- Claude Code handles: actual coding, content generation, deployment

Ensure Claude Code's settings.json routes through cc-switch:
```json
{
  "model": "deepseek-v4-flash",
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:15721",
    "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED",
    "ANTHROPIC_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash"
  }
}
```

## Pitfalls

- **System python3 is broken on this machine** (exit code 49, no output). Always use `/d/Hermes/portable-hermes-agent/python_embedded/python.exe` for Python document generation.
- **GitHub API may be blocked** — use `ddgs text -k "..."` (DuckDuckGo search) instead of `gh search` or `curl api.github.com`.
- **User's "桌面" means D:\Desktop** — check memory for desktop path preferences.
- **WorkBuddy may be at C:\Users\Windows\WorkBuddy with junction to D:\WorkBuddyData** — search both locations.
- **Encoding issues with python-docx**: Remove emoji characters and use explicit `# -*- coding: utf-8 -*-` header when writing scripts to temp files.
