---
name: cpi-ethics-thesis-generation
description: "Generate a full master's thesis paper (Chinese + English Word docs) from WPS Cloud docx drafts, CPI Excel data files, and Obsidian wiki literature notes. Combines statistical analysis, ethical frameworks, and multi-source document generation."
category: research
triggers:
  - thesis generation
  - academic paper
  - CPI data
  - Obsidian wiki
  - Word document generation
  - 硕士论文
  - 论文生成
---

# CPI Ethics Thesis Generation

Generate a complete master's thesis paper (Chinese + English .docx) by combining:

1. An existing docx draft (from WPS Cloud, WorkBuddy, etc.)
2. Real CPI Excel data (10+ years of .xls files)
3. Obsidian wiki markdown notes (literature review, theory frameworks)
4. Statistical analysis (descriptive stats, correlation, regression, clustering)

## Workflow

### Step 1: Find the source file

The draft may be in non-standard paths:

```bash
# WPS Cloud cache
find /c/Users/*/WPS\ Cloud\ Files/ -name "*keyword*" 2>/dev/null

# WorkBuddy project directories  
find /c/Users/*/WorkBuddy/ -name "*keyword*" -o -name "*伦理*" 2>/dev/null

# Recent files shortcut
ls /c/Users/*/AppData/Roaming/Microsoft/Windows/Recent/*keyword* 2>/dev/null
```

### Step 2: Read the docx content

```python
from docx import Document
doc = Document(path)
for p in doc.paragraphs:
    if p.text.strip():
        print(f"[{p.style.name}] {p.text[:200]}")
for table in doc.tables:
    print(f"Table: {len(table.rows)}r x {len(table.columns)}c")
    for row in table.rows:
        print([c.text[:30] for c in row.cells])
```

### Step 3: Extract CPI data from Excel files

CPI data is usually stored in `.xls` format (not `.xlsx`). Use `xlrd`:

```python
import xlrd, os, glob

path = r"D:\...\CPI\2016-2025CPI"
files = sorted(os.listdir(path))

for fname in files:
    fpath = os.path.join(path, fname)
    wb = xlrd.open_workbook(fpath)
    sheet = wb.sheet_by_index(0)
    year = fname.split('.')[1][:4]

    # Standard CPI table layout:
    # Row 9 = header (base year = 100, last month = 100, same month last year = 100)
    # Row 10 = 居民消费价格总指数 (code 1100000000)
    # Col index 6 = 上年同月=100 (yoy same month)
    # Col index 7 = 上年同期=100 (yoy cumulative)

    total_cpi = float(sheet.cell_value(10, 6))  # yoy same month
    total_cpi_yoy = float(sheet.cell_value(10, 7))  # yoy cumulative
```

**Key data structure notes:**
- 2016-2020 files: base year = 2015=100, column headers in row 9
- 2021-2025 files: base year = 2020=100, different subcategory numbering
- `居民消费价格总指数` (2016-2020) vs `居民消费价格指数` (2021-2025)
- Tourism items: `旅行社收费`, `飞机票`, `景点门票`, `宾馆住宿`, `其他住宿`
- Core CPI items: `服务价格指数`, `消费品价格指数`, `食品烟酒`, `医疗保健`
- Code prefix `1100` = total, `1101` = food, `1102` = clothing, etc.

### Step 4: Read Obsidian wiki for academic references

```python
wiki_base = "/d/my-knowledge-base/wiki/应用伦理/"
for fname in os.listdir(wiki_base):
    if fname.endswith(".md"):
        with open(os.path.join(wiki_base, fname), "r", encoding="utf-8") as f:
            content = f.read()
        # Extract frontmatter tags
        # Extract ## sections as literature summaries
        # Extract reference citations
```

### Step 5: Run statistical analysis

```python
# Key metrics to compute:
# 1. Mean, SD, CV for each category over 10 years
# 2. CAGR (Compound Annual Growth Rate): (last/first)^(1/(n-1))*100 - 100
# 3. Cumulative growth: product of all yoy indices - 100
# 4. Pearson correlation with general index
# 5. Simple linear regression: total_cpi ~ tourism_category
# 6. Hierarchical cluster analysis (Ward method) on annual growth rates
```

### Step 6: Generate Word documents

Use `python-docx` to create properly formatted academic papers:

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, color):
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)

def ap(doc, text, bold=False, size=None, align=None, sb=None, sa=None):
    """Add a paragraph with formatting."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    if bold: run.bold = True
    if size: run.font.size = Pt(size)
    if align == 'c': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if sb: p.paragraph_format.space_before = Pt(sb)
    if sa: p.paragraph_format.space_after = Pt(sa)
    p.paragraph_format.line_spacing = Pt(22)

def make_table(doc, headers, rows, caption=""):
    """Create a styled academic table with dark header row."""
    if caption:
        ap(doc, caption, bold=True, size=11, sb=12, sa=6)
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Table Grid'
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs: r.bold = True; r.font.size = Pt(9)
        set_cell_shading(c, "2F5496")
        for p in c.paragraphs:
            for r in p.runs: r.font.color.rgb = RGBColor(255,255,255)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.rows[ri+1].cells[ci]
            c.text = str(val)
```

### Step 7: Paper structure (Chinese version)

```
Title page → 中文摘要+关键词 → English Abstract+Keywords →
一、问题的提出 (现实背景/理论缺口/核心研究问题)
二、理论框架 (Thiroux伦理原则/Sen-Nussbaum能力方法/分析框架)
三、数据与研究设计 (数据来源/核心指标/统计方法)
四、实证发现与伦理审视 (描述统计/涨幅分析/相关回归/聚类/伦理审视)
五、结论与政策建议 (结论/建议/研究局限)
参考文献
```

### Step 8: Ethical framework mapping

Thiroux's five principles mapped to tourism consumption justice:

| Principle | Tourism Justice Mapping |
|-----------|------------------------|
| Value of Life | Tourism as spiritual need, relates to quality of life |
| Goodness/Rightness | Balance between social welfare and consumer rights |
| Justice | Equal tourism opportunities across income groups |
| Truthfulness | Transparent pricing, no hidden fees |
| Individual Freedom | Free choice of tourism consumption |

Sen-Nussbaum capability approach: "nominal purchasing power → actual capabilities → functionings"

### Key metrics for journal targeting

| Metric | Target Range | Journal Fit |
|--------|-------------|-------------|
| Tourism CPI CAGR vs general CPI gap | 1.5-3x gap = significant | 统计类CSSCI |
| CV > 10% for tourism items | High volatility | 旅游类CSSCI |
| Correlation r < 0.5 (insignificant) | Independent price path | 伦理/综合类 |
| 3-cluster structure in hierarchical analysis | Structural differentiation | 所有目标 |

### Pitfalls

1. **WPS Cloud files** are in `C:\Users\xxx\WPS Cloud Files\.xxx\cachedata\GUID\filename.docx` — hard to find by name alone
2. **.xls vs .xlsx**: Old Excel format (`.xls`) requires `xlrd`; newer `.xlsx` uses `openpyxl`
3. **Base year changes**: CPI data changes base year periodically (e.g., 2015 base → 2020 base). Adjust cumulative calculations accordingly
4. **Column indices**: Verify column positions in each file — they may shift when base year changes
5. **python-docx on Windows path issues**: Use `D:/path/` (forward slash) not `/d/path/` (Git Bash style) for file save paths
6. **Unicode in filenames**: When naming .docx files with Chinese characters, use Python's unicode escapes or set the filename from within Python (not shell cp/mv)
7. **PIP env conflict on Windows**: Clear `PIP_PREFIX`, `PIP_TARGET`, `PYTHONPATH` before `pip install` in embedded Python environments
