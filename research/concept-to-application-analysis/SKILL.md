---
name: concept-to-application-analysis
description: "从学术/哲学概念出发，生成概念x当代社会现象的关联应用方案，为每个方案匹配系统研究方法论，并映射到可执行技能（Hermes Skills），输出结构化 Word 文档。"
category: research
triggers:
  - 哲学家x现象
  - 概念应用
  - 哲学与现实
  - 理论联系实际
  - philosopher-society connection
  - concept to application
---

# Concept-to-Application Analysis

从学术/哲学概念出发，生成有深度的应用方案，并匹配系统方法论和可执行技能。

## 适用场景

- 用户拥有一个学术/哲学知识库（如 Obsidian 应用伦理知识库）
- 需要从文献中提取核心概念，映射到当代社会现象
- 需要为每个映射方案提供系统研究方法论
- 需要将方法论方案映射到可执行的工具/技能
- 最终输出为结构化 Word 文档

## 五步工作流

### 第一步：发现知识库

定位用户的知识库位置：

```bash
# Obsidian vault 常见位置
ls ~/Documents/Obsidian\ Vault/
ls /d/my-knowledge-base/
ls ~/my-knowledge-base/

# 查看 vault 结构
find /d/my-knowledge-base/ -name "*.md" -type f -not -path "*/.venv/*" -not -path "*/node_modules/*" | head -50
```

### 第二步：阅读核心文献

系统阅读知识库中的关键文档：

1. **知识图谱/总览文件先看** — 快速掌握全局结构
2. **理论根基类文件** — 提取核心概念和哲学家脉络
3. **应用领域类文件** — 了解已有的应用方向
4. **记录关键标签** — tags 行通常包含哲学家关键词

```bash
# 搜索哲学家关键词
grep -rli "康德\|马克思\|亚里士多德\|胡塞尔\|弗雷格\|布伦塔诺\|克里普克\|公孙龙" /d/my-knowledge-base/wiki/ --include="*.md"
```

### 第三步：生成概念×现象关联

为每个哲学家/概念生成一个关联方案，格式如下：

```
方案 N. 哲学家名称 × 当代社会现象

核心理念：核心概念名称
分析：哲学概念 + 社会现象的深层联系（200-300字）
应用方案：具体的应用方向或工具设计
```

**匹配原则：**
- 概念与社会现象之间有**真关联**，不是强行拼凑
- 概念的核心理论要点要在分析中体现
- 应用方案要有可操作性，不是空泛建议
- 覆盖不同哲学家流派以展示多样性

### 第四步：匹配系统方法论

为每个方案分析需要的系统方法：

```
【方法论框架】
1. 主要方法名称 — 如"伦理评估量表开发"、"数据溯源技术"
2. 具体步骤 — 3-6个可操作的研究/实施步骤
3. 技术细节 — 方法的具体操作说明
4. 验证方式 — 如何验证方法的有效性
```

常见方法论类型：
- 量表开发与验证
- 实验设计（准实验、真实验）
- 质性研究（现象学访谈、扎根理论）
- 技术方案设计（溯源协议、保护框架）
- 算法公平性评估
- 社会网络分析
- 认知科学实验

### 第五步：筛选并映射技能

从可用 Skills 列表中筛选合适的技能：

```python
# 查看所有可用技能
skill_view(name)  # 加载重点技能
skills_list()     # 浏览所有技能

# 常用技能映射参考
# generate-architecture-docs    → 框架/架构文档输出
# excalidraw                    → 流程图/概念图可视化
# research-synthesis-...        → 文献综合与研究方向生成
# instructor                    → 结构化数据提取与评估
# dspy                          → 系统化 AI 流水线
# outlines                      → 约束生成与 Schema 验证
# systematic-debugging          → 根因分析与问题诊断
# jupyter-live-kernel           → 交互式数据分析
# chroma                        → 向量搜索与语义相似度
# feynman-docx-educational-guide → 教育型文档生成
```

为每个方案建立技能映射表：

| 技能 | 作用 | 说明 |
|------|------|------|
| [GEN] | 生成架构文档 | 输出完整框架设计 |
| [EXD] | 绘制流程图 | 可视化模型/流程 |

### 第六步：生成结构化 Word 文档

使用 python-docx 生成专业 Word 文档：

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

def set_run_font(run, name="Microsoft YaHei", size=11, bold=False, color=None, italic=False):
    """设置中文字体，确保中文正确渲染"""
    ...

def set_cell_shading(cell, color):
    """设置表格单元格底色"""
    ...
```

文档结构：
1. **标题页** — 大标题 + 副标题 + 来源说明
2. **技能图例** — 所有用到的技能缩写对照表
3. **每项方案**（循环）：
   - H2: 编号. 哲学家 × 现象
   - 核心理念（加粗）
   - 分析正文
   - 应用方案（缩进，蓝色标记）
   - 系统方法标题（红色）
   - 方法框架详情（等宽块）
   - 技能映射表（三列表格，彩色行）
4. **页脚**

### 保存路径

注意用户对"桌面"的偏好：
```python
# 默认
desktop = os.path.expanduser("~/Desktop")
# 或用户指定的路径（如 D:/Desktop）
desktop = "D:/Desktop"
path = os.path.join(desktop, "文件名.docx")
```

## 知识库的常见结构

### Obsidian vault 可能的位置
- `~/Documents/Obsidian Vault/`
- `/d/my-knowledge-base/`
- 或用户自定义位置（检查 `OBSIDIAN_VAULT_PATH` 环境变量）

### 应用伦理类 vault 的典型三层结构
```
一层：理论根基（伦理学学派、分析哲学、应用伦理基础）
二层：应用领域（AI伦理、数字政府、数据伦理）
三层：实践场域（统计调查、旅游伦理、专题研究）
```

### 哲学家关键词标签
从 Obsidian 笔记的 tags 行和文件名中提取：
```yaml
tags: #康德 #现象学 #马克思主义 #弗雷格 #分析哲学
```

## 注意事项

1. **先读知识图谱** — 总览文件能快速了解知识库的整体结构和覆盖范围
2. **不重复已有内容** — 检查用户是否已经整理过类似的主题
3. **概念要有真关联** — 避免强行拼接，每个关联都要有明确的理论依据
4. **方法要可操作** — 方法论必须有具体的技术路径，不能空泛
5. **技能要匹配实际** — 只映射实际存在且可用的技能，不要假设用户有未安装的工具
6. **Obsidian vault 可能有 [[wiki-link]]** — 这些是 Obsidian 内部的交叉引用链接
7. **文件路径注意 Windows 混用斜杠** — 使用 `os.path.join()` 和纯正斜杠路径

## 输出示例

完成后的 Word 文档包含：
- 10个哲学×社会现象的关联方案
- 每个方案的分析、应用方案、系统方法框架
- 技能映射表（技能缩写 + 作用 + 说明）
- 技能图例（缩写与全称对照）
- 专业排版（微软雅黑、蓝色主题、交替行底色）
