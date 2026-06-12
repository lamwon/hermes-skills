---
name: research-synthesis-thesis-brainstorming
description: "Systematic methodology for synthesizing local literature, knowledge base (Obsidian), and real-world datasets to generate novel interdisciplinary thesis directions. Use when the user needs thesis brainstorming that genuinely combines their existing resources."
category: research
triggers:
  - thesis brainstorming
  - research synthesis
  - 破题
  - 论文方向
  - interdisciplinary research
---

# Research Synthesis: Thesis Brainstorming Methodology

A systematic approach that combines three resource streams to generate novel, data-grounded thesis directions.

## The Three-Stream Method

```
Stream A: Local Literature    Stream B: Knowledge Base      Stream C: Real Data
(学术论文PDFs, docx)           (Obsidian vault, wiki)         (Excel, CSV, databases)
```

### Step 1: Discover All Resources

Search across all three streams simultaneously:

```bash
# Stream A: Academic papers
find /d/ -name "*.pdf" -path "*论文*" 2>/dev/null
find /d/ -name "*.pdf" -path "*文献*" 2>/dev/null

# Stream B: Knowledge base (Obsidian)
find /d/ -path "*/.obsidian/*" -name "*.md" 2>/dev/null
find /d/my-knowledge-base/ -name "*.md" 2>/dev/null

# Stream C: Real data
find /d/ -name "*CPI*" -o -name "*数据*" 2>/dev/null
find /d/ -name "*.xls*" -o -name "*.csv" 2>/dev/null | head -30
```

### Step 2: Read Knowledge Base Core

Read the wiki/notes systematically:
- Knowledge graphs first (they show the full picture)
- Per-topic notes (AI ethics, tourism ethics, statistics ethics)
- Existing thesis work (so you don't duplicate)

### Step 3: Extract Real Data

For Excel files (.xls/.xlsx), install xlrd if needed:

```bash
# On Windows with embedded Python, clear env vars first:
PIP_PREFIX= PIP_TARGET= PYTHONPATH= python -m pip install xlrd
```

Read data and extract key patterns:
```python
import xlrd, os
wb = xlrd.open_workbook(filepath)
sheet = wb.sheet_by_index(0)
# Find key rows (e.g., "居民消费价格总指数" at row index 10)
# Extract time series for analysis
```

### Step 4: Identify Data-Driven Patterns

Look for patterns in the data that connect to the literature:
- **Anomalies**: spikes, dips, structural breaks (e.g., 2019 food price surge in CPI)
- **Divergences**: categories moving differently (e.g., service vs consumer goods pricing)
- **Gaps**: what the data shows but the literature hasn't covered

### Step 5: Generate Novel Thesis Directions

For each direction, force yourself to answer:
1. **What data from Stream C directly supports this?** (Must cite specific columns/rows)
2. **What theory from Stream A/B directly connects?** (Must cite specific papers/notes)
3. **What simple statistical model can test the hypothesis?**
4. **What journal would publish this intersection?**

### Key Principles

1. **Don't repeat existing directions** — first read what the user already has (their existing thesis notes)
2. **Forbid "data-less" directions** — every direction MUST use at least one measurable indicator from the real data
3. **Cross-reference everything** — each direction should explicitly cite: specific data points + specific literature citations + specific statistical method
4. **Include a comparison table** — across dimensions: data needs, model complexity, theory depth, timeline

### Practical Tips

- On Windows, `PIP_PREFIX= PIP_TARGET= PYTHONPATH= python -m pip install xlrd` is needed due to embedded Python env var conflicts
- Obsidian vaults often have `[[wiki-link]]` style cross-references in `.md` files
- CPI data in Chinese government format: row 10="居民消费价格总指数", col 6="上年同月=100", col 7="上年同期=100"
- For `.docx` files, use python-docx; for `.pdf`, extract text with pymupdf
