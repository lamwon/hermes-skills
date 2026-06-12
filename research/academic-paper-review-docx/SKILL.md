---
name: academic-paper-review-docx
description: 对中文学术论文（.docx）进行专业审稿，将审稿意见以红色字体标注在原文档中，原路径保存并重命名加"（审稿意见）"。适用于本科/硕士论文审阅。
tags: [academic-review, thesis, docx, python-docx, chinese, paper-review]
---

# Academic Paper Review with Red Annotations (.docx)

对中文本科/硕士论文进行结构化审稿，审稿意见以**红色字体**嵌入原文档。

## Workflow Overview

```
1. read_file/skill_view → 提取论文全文结构
2. 调用 awesome-ai-research-writing 技能模板进行审稿
3. 编写 Python 脚本 → python-docx 逐段插入红色审稿意见
4. 保存为 "原文件名（审稿意见）.docx"
```

## Step 1: 提取论文内容

先用 Python 提取 .docx 全文，了解结构和内容：

```python
# -*- coding: utf-8 -*-
import docx
path = r'D:\path\to\论文.docx'
doc = docx.Document(path)
for i, p in enumerate(doc.paragraphs):
    text = p.text.strip()
    if text:
        style = p.style.name if p.style else "None"
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"[P{i}|{style}] {preview}")
```

**关键**: 必须在文件开头加 `# -*- coding: utf-8 -*-`，否则嵌入 Python 沙箱会因 GBK 编码报错。且不能通过 `execute_code` 沙箱运行含中文的脚本，必须写入 .py 文件后用 terminal 运行。

## Step 2: 审稿内容结构

按以下六个维度组织审稿意见：

| 维度 | 关注点 |
|------|--------|
| 摘要与关键词 | 完整性、数据支撑、学术化表述 |
| 绪论 | 政策引用精确度、研究目的明确性、方法描述 |
| 理论基础与文献综述 | 理论完整性、文献覆盖面、评述逻辑 |
| 研究设计与数据分析 | 信效度、样本量、数据呈现、方法规范性 |
| 策略建议 | 可操作性、数据支撑、创新性 |
| 结论与展望 | 逻辑闭环、局限诚实性、展望前瞻性 |

每条意见应包含：
- **肯定性评价**（亮点/优点）
- **具体问题**（指出位置、引用原文）
- **修改建议**（可操作的具体改进方案）

## Step 3: 编写审稿脚本

核心方法：

```python
# -*- coding: utf-8 -*-
import docx
from docx.shared import Pt, RGBColor

SRC = r'原文件路径.docx'
DST = r'原文件路径（审稿意见）.docx'
doc = docx.Document(SRC)
RED = RGBColor(0xFF, 0x00, 0x00)

def add_inline_comment(para, comment_text):
    """在段落内追加红色批注（简单方法）"""
    run = para.add_run(f"\n【审稿意见】{comment_text}")
    run.font.color.rgb = RED
    run.font.size = Pt(10)
    run.font.bold = True

# 审稿意见列表: [(段落索引, "节标题", "意见内容"), ...]
reviews = [
    (idx, "标题", "意见正文"),
    ...
]

# 逐段插入
for idx, anchor, comment in reviews:
    para = doc.paragraphs[idx]
    add_inline_comment(para, comment)
```

## Step 4: 整体评价

在文档末尾（或致谢/参考文献前）添加整体评价，包含对以下维度的星级评定和综合评分：

- 选题价值
- 理论框架
- 研究方法
- 数据分析
- 策略建议
- 写作规范

## Pitfalls

1. **GBK 编码陷阱**: execute_code 沙箱运行含中文的 Python 脚本会报 `SyntaxError: Non-UTF-8 code starting with`。对策：写入 .py 文件后用 terminal 运行，且清除 `PIP_PREFIX PIP_TARGET PYTHONPATH` 环境变量。
2. **段落索引变化**: 在 doc.paragraphs 中间插入新段落会导致后续索引偏移。对策：使用 `add_inline_comment()` 在段落末尾追加文本（不添加新段落），或在确信不会移位时从后往前插入。
3. **python-docx 限制**: 不支持直接在某段落前插入新段落。如需在特定位置前添加，需操作底层 XML（较复杂）。简便方案：统一用 `add_run()` 追加在段尾。
4. **红字可读性**: 红色标注后，原文字体颜色不变。建议审稿意见用 `bold=True` + 红色增强辨识度。
5. **表格处理**: python-docx 的 `doc.tables` 包含表格数据，如需审阅表格内容，需分别遍历表格的 `rows > cells > paragraphs`。

## Prerequisites

```bash
pip install python-docx   # 需要在系统 Python 中安装，非嵌入版
```
