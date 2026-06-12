---
name: generate-architecture-docs
description: Generate professionally-formatted Word documents (.docx) containing software architecture designs, multi-agent prompt schemes, and system frameworks. Creates styled documents with colored tables, code blocks, hierarchical headings, and structured content via python-docx.
version: 1.0.0
author: Hermes Agent
tags: [documentation, architecture, word, docx, prompt-scheme, design]
---

# Generate Architecture Design Documents (.docx)

Generate professional Word documents with software architecture frameworks, multi-agent prompt schemes, and system design documentation using python-docx.

## When to Use

Use this skill when:
- You need to produce a professionally formatted `.docx` document describing a system architecture
- You're designing a multi-agent system and need prompt schemes for each agent role
- The user asks for structured documentation with tables, code blocks, and headings
- You need to create Chinese-language technical documentation with mixed formatting
- Output must go to a specific user-specified path (e.g., ~/Desktop/claude code/)

## Prerequisites

```bash
pip install python-docx
```

## Document Components Recipe

Build each document with this reusable pattern. The helper functions below go in a Python script that generates the .docx.

### 1. Helper Functions (copy these)

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

def set_cell_shading(cell, color):
    shading = cell._element.get_or_add_tcPr()
    shading_elem = shading.makeelement(qn('w:shd'), {
        qn('w:val'): 'clear',
        qn('w:color'): 'auto',
        qn('w:fill'): color
    })
    shading.append(shading_elem)

def add_styled_table(doc, headers, rows, header_color="2B579A"):
    """Add a table with colored header row and alternating row shading."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                r.font.size = Pt(10)
        set_cell_shading(cell, header_color)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.rows[ri + 1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
            if ri % 2 == 1:
                set_cell_shading(cell, "E8EFF7")
    return table

def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x3C, 0x6E)
    return h

def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(6)
    return p

def add_code_block(doc, code, font_size=8):
    """Add a monospace code block paragraph."""
    p = doc.add_paragraph()
    run = p.add_run(code)
    run.font.size = Pt(font_size)
    run.font.name = 'Courier New'
    return p

def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(text, style='List Bullet')
    p.paragraph_format.left_indent = Cm(1.27 + level * 1.27)
    p.paragraph_format.space_after = Pt(2)
    return p
```

### 2. Standard Document Template

```python
def build_document(title, subtitle, sections, output_path):
    """Generate a structured .docx document.

    Args:
        title: Document title (Heading 0, centered)
        subtitle: Subtitle text (centered, gray)
        sections: list of (heading_text, heading_level, content_items)
            content_items can be: "body:..." | "table:hdr1,hdr2|row1a,row1b|..." | "code:..." | "bullet:..."
        output_path: full path for the .docx file
    """
    doc = Document()

    # Title
    t = doc.add_heading(title, level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in t.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x3C, 0x6E)

    # Subtitle
    s = doc.add_paragraph(subtitle)
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in s.runs:
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_paragraph(f'Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}')

    for heading_text, level, items in sections:
        add_heading(doc, heading_text, level=level)
        for item in items:
            if item.startswith("body:"):
                add_body(doc, item[5:])
            elif item.startswith("table:"):
                parts = item[6:].split("|")
                headers = parts[0].split(",")
                rows = [p.split(",") for p in parts[1:]]
                add_styled_table(doc, headers, rows)
            elif item.startswith("code:"):
                add_code_block(doc, item[5:])
            elif item.startswith("bullet:"):
                add_bullet(doc, item[7:])

    doc.save(output_path)
    return output_path
```

## Full Workflow

### Step 1: Check & Install Dependencies
```bash
pip install python-docx
```

### Step 2: Design the Architecture
Before writing code, design the full framework:
- What are the system dimensions/domains? (e.g., 8-dimension closed loop: command, coordination, division of labor, support, design, supervision, control, acceptance)
- What agent roles are needed? (Orchestrator, Style Agent, Painter Agent, NLP Agent, etc.)
- What skills/tools map to each role?
- What are the quality gates at each stage?

### Step 3: Map Skills to Architecture
Create a skill mapping table showing:
- Skill name
- Purpose in this project
- Which architecture layer it belongs to
- How to invoke it (terminal, delegate_task, etc.)

### Step 4: Write Agent Prompt Templates
For each agent role, write:
- System prompt (persona, capabilities, constraints)
- Task prompt (what to do with specific inputs)
- Output format (JSON schema or structured text)
- Quality checklist

### Step 5: Write the Generation Script
Compose a Python script that calls the helper functions to produce the .docx. Structure it as:

```python
def build_doc_A():
    """Document 1: Hermes Agent prompt scheme"""
    doc = Document()
    # ... add sections with heading/body/table/code helpers
    doc.save(path_A)

def build_doc_B():
    """Document 2: Claude Code prompt scheme"""
    # ... same pattern

if __name__ == "__main__":
    build_doc_A()
    build_doc_B()
    print("Done!")
```

### Step 6: Save to Target Path
```python
DESKTOP = os.path.expanduser("~/Desktop/claude code")
os.makedirs(DESKTOP, exist_ok=True)
doc.save(os.path.join(DESKTOP, "filename.docx"))
```

## Three-Phase Content Structure (For Multi-Agent Systems)

When documenting a multi-agent system with two AI orchestrators, use this parallel structure:

### Document A: Primary Agent (Orchestrator) Prompt Scheme
| Section | Content |
|---------|---------|
| Overview | Core capabilities, tech stack, design philosophy |
| Architecture | System dimensions/domains with closed-loop guarantees |
| Skill Map | All skills each with purpose, layer, invocation |
| Orchestrator Prompts | System prompt, task decomposition, requirements parsing |
| Agent Prompts | Per-role: Style, Painter, NLP, Prompt, Code, Review |
| Reviewer Prompts | Spec compliance, code quality, design quality |
| Workflow | Phase-by-phase execution plan |
| Constraints | Iteration, communication, quality, design principles |

### Document B: Implementation Agent (Coding Agent) Prompt Scheme
| Section | Content |
|---------|---------|
| Role Definition | Responsibilities vs. not-responsibilities |
| Startup Config | CLI parameters, init prompt template |
| Module Prompts | Per-module: engine, LLM, config, installer with code stubs |
| Test Strategy | Unit test structure, integration test examples |
| Parallel Strategy | Multi-instance launch template, dependency matrix |
| Collaboration | Communication flow diagram, error recovery |
| Troubleshooting | Common issues and solutions |

## Pitfalls

1. **python-docx not installed**: Check with `python3 -c "from docx import Document"` before writing the script. Install with `pip install python-docx`.

2. **Chinese/Unicode encoding in terminal**: The terminal may show garbled Chinese due to `gbk` codec, but `.docx` files store Unicode correctly. Don't worry about terminal display — verify by actually opening the file.

3. **Code blocks in Word**: Use `Courier New` font at 7-8pt for code blocks. If code is very long, break into multiple `add_code_block` calls with section headers.

4. **Table rendering**: Always set `table.style = 'Table Grid'` otherwise borders won't render. Always call `set_cell_shading` for header rows.

5. **Long execution**: A script generating 2+ documents with 50+ sections each takes ~5 seconds. Use a generous timeout on the terminal call.

6. **File path**: Always use `os.path.expanduser()` for `~/` paths. On Windows, `~/Desktop/claude code` maps to `C:\Users\<user>\Desktop\claude code`.

## Verification

After generating, verify the output:
```python
from docx import Document
doc = Document(path)
print(f"{len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables")
# Check all major headings exist
headings = [p.text for p in doc.paragraphs if p.style.name.startswith('Heading')]
```
