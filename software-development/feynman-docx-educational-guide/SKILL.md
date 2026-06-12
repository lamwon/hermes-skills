---
name: feynman-docx-educational-guide
description: Generate a Feynman-style educational Word document (.docx) with embedded statistical charts for any collection of Python packages/models. Uses matplotlib/seaborn to generate real data visualizations, runs actual model inference (PyMC, Prophet) for authentic charts, and embeds everything with python-docx.
tags: [docx, feynman, educational, matplotlib, statistics, python-docx, visualization]
---

# Feynman-Style Educational .docx Generator

Create a comprehensive Word document explaining Python packages/models using the Feynman Technique — simple language, real examples, and actual data visualizations.

## When to use

- User asks to "explain" or "teach" a set of Python packages or models
- Need a polished .docx with embedded charts, code examples, and structured explanations
- Want to generate REAL statistical charts (not placeholders) — running actual model fitting

## Template structure per package

Each package gets this structure in the document:

```
1. 🧠 一句话概念 (Feynman one-liner)
2. 核心能力 (bullet list of key features)
3. 📖 生活类比 (everyday analogy)
4. 📊 图表 (real matplotlib/seaborn chart generated from data)
5. 💻 代码示例 (copy-paste ready code blocks)
```

## Implementation steps

### 1. Generate charts with matplotlib (save to temp dir)

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tempfile, os

OUT_DIR = tempfile.mkdtemp()

def savefig(name):
    path = os.path.join(OUT_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=130, bbox_inches='tight')
    plt.close()
    return path
```

For each package, create a chart that VISUALLY demonstrates its core concept:

- **scipy**: Normal distributions overlapping (explains t-test visually)
- **statsmodels**: Regression line with confidence interval band
- **seaborn**: Correlation heatmap from a real dataset
- **pingouin**: ANOVA group comparison with mean lines and scatter
- **pymc**: Prior vs likelihood vs posterior distributions
- **prophet**: Actual time series forecast with uncertainty bands (runs Prophet model)
- **pomegranate**: GMM clustering of 2D blobs
- **arviz**: MCMC trace plots + posterior histograms (runs actual PyMC sampling)
- **bambi**: Hierarchical model showing per-group means vs grand mean

### 2. Create the Word document

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

def add_section(doc, title, feynman_q, what, features, analogy,
                code_blocks, img_path=None):
    doc.add_heading(title, level=1)
    # Feynman one-liner
    p = doc.add_paragraph()
    r = p.add_run('🧠 用一句话说清楚：')
    r.bold = True; r.font.color.rgb = RGBColor(0x1A, 0x6B, 0xB5)
    p.add_run(feynman_q).italic = True

    # Image
    if img_path and os.path.exists(img_path):
        doc.add_picture(img_path, width=Inches(5.5))

    # Features
    doc.add_heading('核心能力', level=2)
    for f in features: doc.add_paragraph(f, style='List Bullet')

    # Analogy
    doc.add_heading('📖 生活类比', level=2)
    doc.add_paragraph(analogy)

    # Code
    doc.add_heading('💻 使用方法', level=2)
    for block in code_blocks:
        p = doc.add_paragraph()
        p.add_run(block['title']).bold = True
        code_p = doc.add_paragraph()
        code_p.paragraph_format.left_indent = Cm(0.8)
        cr = code_p.add_run(block['code'])
        cr.font.name = 'Consolas'; cr.font.size = Pt(8.5)
```

### 3. Run REAL models for authentic charts

For credibility, run actual model fitting to generate charts:

```python
# Prophet example — runs real forecasting
from prophet import Prophet
m = Prophet()
m.fit(df_prophet)
forecast = m.predict(m.make_future_dataframe(periods=60))

# PyMC example — runs actual MCMC sampling
import pymc as pm
with pm.Model() as model:
    a = pm.Normal("alpha", 0, 10)
    b = pm.Normal("beta", 0, 10)
    sigma = pm.HalfNormal("sigma", 1)
    pm.Normal("obs", a + b * x, sigma, observed=y)
    trace = pm.sample(800, tune=400, progressbar=False, cores=1)
```

### 4. Add summary comparison table

```python
table = doc.add_table(rows=N+1, cols=4)
table.style = 'Light Grid Accent 1'
headers = ['场景', '推荐包', '原因', '口诀']
# ... fill rows with scene -> package -> reason -> slogan mapping
```

### 5. Save

```python
doc.save(output_path)
```

## Tips

- **matplotlib backend**: Always set `matplotlib.use('Agg')` when running non-interactively to avoid display errors.
- **Chinese fonts**: Set `plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']` for Chinese labels. Fallback to DejaVu Sans ensures ASCII fallback.
- **Axes Unicode minus**: Set `plt.rcParams['axes.unicode_minus'] = False` to prevent minus signs from rendering as boxes.
- **PyMC sampling**: Use `cores=1, progressbar=False` to avoid multiprocessing issues on Windows embedded Python.
- **Temp dir**: Use `tempfile.mkdtemp()` for chart output, then clean up after (not critical — temp dirs are auto-cleaned on reboot).
- **File size**: A document with 9 embedded charts at 130 DPI will be ~500-600KB.
