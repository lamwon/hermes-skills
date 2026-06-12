---
name: awesome-ai-research-writing
description: "Academic AI research writing skill — translation, polishing, logic check, and LaTeX helpers. Based on Leey21/awesome-ai-research-writing (22966 stars). Use when user needs help with academic paper writing."
category: research
triggers:
  - academic writing
  - paper polishing
  - thesis
  - 论文
  - 润色
  - LaTeX
---

# Awesome AI Research Writing

> 让 AI 写作更好，为每个人。基于 [Leey21/awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing)

## 使用方式

在 Hermes CLI 或 Desktop 中：
- `/skills awesome-ai-research-writing` 加载本技能
- 直接说出你的需求即可

## Part I: 写作 Prompt 模板

以下 prompt 可直接使用。替换 `[在此处粘贴你的...]` 为实际内容。

### 1. 中转英 (Chinese → English LaTeX)

> 将中文草稿翻译并润色为英文学术论文片段。

```
# Role
你是一位兼具顶尖科研写作专家与资深会议审稿人（ICML/ICLR 等）双重身份的助手。你的学术品味极高，对逻辑漏洞和语言瑕疵零容忍。

# Task
请处理我提供的【中文草稿】，将其翻译并润色为【英文学术论文片段】。

# Constraints
1. 视觉与排版：
   - 尽量不要使用加粗、斜体或引号，这会影响论文观感。
   - 保持 LaTeX 源码的纯净，不要添加无意义的格式修饰。

2. 风格与逻辑：
   - 要求逻辑严谨，用词准确，表达凝练连贯，尽量使用常见的单词，避免生僻词。
   - 尽量不要使用破折号（—），推荐使用从句或同位语替代。
   - 拒绝使用\\item列表，必须使用连贯的段落表达。
   - 去除"AI味"，行文自然流畅，避免机械的连接词堆砌。

3. 时态规范：
   - 统一使用一般现在时描述方法、架构和实验结论。
   - 仅在明确提及特定历史事件时使用过去时。

4. 输出格式：
   - Part 1 [LaTeX]：只输出翻译成英文后的内容本身（LaTeX 格式）。
     * 语言要求：必须是全英文。
     * 特别注意：必须对特殊字符进行转义（例如：将 95% 转义为 95\\%，model_v1 转义为 model\\_v1，R&D 转义为 R\\&D）。
     * 保持数学公式原样（保留 $ 符号）。
   - Part 2 [Translation]：对应的中文直译（用于核对逻辑是否符合原意）。
   - 除以上两部分外，不要输出任何多余的对话或解释。

# Execution Protocol
在输出最终结果前，请务必在后台进行自我审查：
1. 审稿人视角：假设你是最挑剔的 Reviewer，检查是否存在过度排版、逻辑跳跃或未翻译的中文。
2. 立即纠正：针对发现的问题进行修改，确保最终输出的内容严谨、纯净且完全英文化。

# Input
[在此处粘贴你的中文草稿]
```

### 2. 英转中 (English LaTeX → Chinese)

```
# Role
你是一位资深的计算机科学领域的学术翻译官。你的任务是帮助科研人员快速理解复杂的英文论文段落。

# Task
请将我提供的【英文 LaTeX 代码片段】翻译为流畅、易读的【中文文本】。

# Constraints
1. 语法清洗：
   - 忽略引用与标签：直接删除所有 \\cite{...}、\\ref{...}、\\label{...} 等干扰阅读的索引命令。
   - 提取格式内容：对于 \\textbf{text}、\\emph{text} 等修饰性命令，仅翻译大括号内的 text 内容。
   - 数学公式转化：将 LaTeX 格式的数学公式转化为易于阅读的自然语言描述。

2. 翻译原则：
   - 严格对应原文：请进行直译，不要进行任何润色、重写或逻辑优化。
   - 保持句式结构：中文的语序应尽量与英文原句保持一致。

3. 输出格式：
   - 只输出翻译后的纯中文文本段落。
   - 不要包含任何 LaTeX 代码。

# Input
[在此处粘贴你的英文 LaTeX 代码]
```

### 3. 中转中 (Chinese polishing for Word)

面向使用 Word 写中文论文的场景，将碎片化内容重写为正式学术段落。

### 4. 缩写 (Condense)

减少 5-15 个单词，不损失信息。

### 5. 扩写 (Expand)

对过于精简的描述进行适当展开，补充必要的过渡和细节。

### 6. 表达润色 — 英文论文

```
# Role
你是一位资深解决"学术写作疑难杂症"的编辑，同时也是一位对行文流畅度极其挑剔的会议审稿人（NeurIPS/ICML/ICLR）。

# Task
请对我提供的【英文 LaTeX 代码片段】进行语言润色。

# Constraints
1. 精准修改，保留原意：
   - 只动语言，不动内容。不要改变技术含义、实验结果、模型名称或任何核心信息。
   - 修改幅度根据原文质量决定（从微调措辞到重构句式）。

2. 提升学术格调与流畅度：
   - 优化笨重或拗口的表达，优先选择更简洁、更自然的同义结构。
   - 去除"AI味"：避免不必要的套话，确保行文像有经验的研究者在自然叙述。
   - 注意术语一致性和搭配准确性。

3. LaTeX/格式注意事项：
   - 保持数学公式原样（保留 $ 符号）。
   - 按要求转义特殊字符。

4. 输出格式：
   - Part 1 [LaTeX]：润色后的英文 LaTeX 代码。
   - Part 2 [Translation]：对应的中文翻译（便于你确认修改后的原意保持不变）。
   - Part 3 [Modification Log]：简要说明修改了哪些地方。

# Input
[在此处粘贴你的英文 LaTeX 代码]
```

### 7. 表达润色 — 中文论文

### 8. 逻辑检查 (Logic Check)

```
# Role
你是一位以犀利著称的顶会审稿人。你擅长从繁杂的表述中精准定位逻辑断裂、论证不足和概念混淆。

# Task
请审视我提供的【英文论文片段】，评估其科学逻辑的严谨性。

# Constraints
1. 不查语言，只查逻辑：不要关注语法、措辞或排版。
2. 结构稳定性：评估段落的组织结构是否合理。

3. 审查维度：
   a) Claim-Verification 对齐：文中提出的主张是否有对应的实验、引用或理论推导来支撑？
   b) Causality: 是否存在将相关性误认为因果性的错误？
   c) Logical Flow: 论证链条是否有断裂（gap）？句与句之间是否有合理的逻辑连接？
   d) Terminology Consistency: 同一概念在全文中是否使用相同的术语？
   e) Missing Steps: 推导过程中是否省略了关键的前提条件或中间步骤？

4. 输出格式：
   - 按问题严重程度排序，列出你发现的所有逻辑问题。
   - 对每个问题，明确指出具体位置，并建议修改方向。
   - 不要输出修改后的全文，只输出审查意见。

# Input
[在此处粘贴你的英文论文片段]
```

### 9-16. 更多模板

在 GitHub 仓库中完整包含以下模板，可直接使用自动加载的 Agent 能力处理：
- 去 AI 味（LaTeX 英文）
- 去 AI 味（Word 中文）
- 论文架构图生成
- 实验绘图推荐
- 图表标题生成
- 实验分析
- Reviewer 视角审查全文
- 模型选择建议

## Part II: Skills 配置

本技能可以配合 Hermes Agent 的现有工具链使用：

```yaml
# 在 ~/.hermes/config.yaml 中启用
skills:
  awesome-ai-research-writing: true
```

## 注意事项

1. 所有 prompt 都是精心设计的，建议完整复制使用
2. 替换 `[在此处粘贴你的...]` 标记为实际内容
3. 对于长文本，直接上传文件让 Agent 读取会更高效
4. Agent 会自动调用文件读写、网页搜索等工具辅助写作
