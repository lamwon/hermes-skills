---
name: obsidian-research-synthesis
description: Discover an Obsidian vault, systematically extract all knowledge notes, and synthesize them into structured reports (Word documents, markdown analyses, or research briefs). Useful for research projects where the user maintains an Obsidian knowledge base.
tags: [obsidian, knowledge-graph, research, report-generation, docx]
---

# Obsidian Research Synthesis Workflow

## When to Use

- User mentions they have notes, a knowledge base, or research materials in Obsidian
- User says "你自己找" (find it yourself) — indicating notes exist but you need to discover them
- A task requires synthesizing information across multiple notes into a coherent report
- User has an Obsidian vault with markdown notes organized by topic

## Discovery Phase

### 1. Find the Vault Location

The Obsidian vault always contains a `.obsidian` subdirectory. Search methods in order:

**Method A — Walk user home directory (fastest, 3-level max):**

```python
import os
home = os.path.expanduser('~')
for root, dirs, files in os.walk(home):
    skip = {'AppData', 'Application Data', 'Cookies', 'Cache', 'Temp', 'tmp',
            '__pycache__', 'node_modules', '.git', 'venv', '.venv'}
    dirs[:] = [d for d in dirs if d not in skip and not d.startswith('.')]
    depth = root.replace(home, '').count(os.sep)
    if depth > 3:
        dirs.clear()
        continue
    if '.obsidian' in os.listdir(root):
        print(f'FOUND: {root}')
        break
```

**Method B — Scan all drive roots (fallback):**

```python
for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
    drive = letter + ':/'
    if os.path.exists(drive) and os.path.isdir(os.path.join(drive, '.obsidian')):
        print(f'FOUND: {drive}')
```

**Method C — Walk all drive roots (most thorough):**

```python
for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
    drive = letter + ':/'
    if not os.path.exists(drive):
        continue
    for item in os.listdir(drive):
        full = os.path.join(drive, item)
        if os.path.isdir(full) and os.path.isdir(os.path.join(full, '.obsidian')):
            print(f'FOUND: {full}')
```

### 2. Map the Vault Structure

```python
import os
vault = r'D:\path\to\vault'
for root, dirs, files in os.walk(vault):
    rel = os.path.relpath(root, vault)
    print(f'{rel}/')
    for f in files:
        size = os.path.getsize(os.path.join(root, f))
        print(f'  {f} ({size}B)')
```

Look for:
- `wiki/` or `notes/` directories — organized markdown knowledge
- `raw/` directories — source documents (PDFs, docs)
- Files with tags like `#知识图谱` `#论文方向` `#总览` in their YAML frontmatter
- Files named like `*知识图谱*`, `*整合*`, `*总览*` — these are hub notes

## Extraction Phase

### 3. Read All Knowledge Notes

Read ALL markdown files systematically. Prioritize:
1. Knowledge graph/summary notes first (they show the big picture)
2. Topic-specific notes second (deep content)
3. Analysis/proposal notes last (synthesis has already happened)

Use `read_file` for each note. Key things to extract:
- YAML frontmatter (aliases, tags) — shows cross-linking
- Mermaid diagrams — show relationship structure
- Wiki links (`[[...]]`) — show note connections
- Key findings and core arguments

### 4. Build a Mental Model

From the extracted notes, construct:
- **Topics/themes**: What knowledge domains are covered?
- **Relationships**: How do topics connect? (theory→practice, problem→solution)
- **Key data points**: Numbers, statistics, literature counts
- **Existing work**: What has already been analyzed or proposed?
- **Gaps**: What's missing or could be improved?

## Synthesis Phase

### 5. Generate Report (Word Document)

Use `python-docx` for structured reports. Typical structure:
1. Background & data foundation (table)
2. Panoramic view with cross-domain findings
3. Critical evaluation of existing work
4. New recommendations with rationale
5. Integration suggestions

**Key `python-docx` patterns:**

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()
style = doc.styles['Normal']
style.font.name = '微软雅黑'  # or 'SimSun', 'Arial'
style.font.size = Pt(11)

# Headings
doc.add_heading('Title', level=0).alignment = WD_ALIGN_PARAGRAPH.CENTER

# Tables with data
table = doc.add_table(rows=N, cols=2, style='Light Shading Accent 1')
for i, (k, v) in enumerate(data):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

# Bold labels
p = doc.add_paragraph()
p.add_run('Bold label: ').bold = True
p.add_run('Normal text')

# Color footer
run = footer.add_run('--- End ---')
run.font.color.rgb = RGBColor(150, 150, 150)
run.font.size = Pt(10)
```

### 6. Generate Report (Markdown)

For Obsidian-native formats, write to a `.md` file in the vault with proper frontmatter:

```markdown
---
created: YYYY-MM-DD
tags: #分析 #报告
---

# Title

Content...
```

## Pitfalls

1. **Obsidian vaults may NOT be at `~` or `Documents/`** — scan all drives, especially `D:\`, `E:\`, etc.
2. **Skip `node_modules`, `__pycache__`, `.git`** in walks — they're huge and irrelevant
3. **`python-docx` uses string concatenation for Chinese text** — be careful with line breaks mid-string: Python's implicit string concatenation only works if both parts are on the same logical line or if the line ends with an unquoted string. Use `'...' '...'` pattern (adjacent literals), not `'...'` + newline + `'...'`.
4. **Git Bash path issues on Windows**: When passing paths with backslashes, use double quotes around the full path: `python "D:\path\to\script.py"`
5. **Clean up temp scripts**: After generation, delete the Python script used to create the report.
6. **YAML frontmatter in Obsidian**: Notes start with `---` then YAML then `---`. Use `read_file` to see it fully; skip the frontmatter if parsing programmatically.
