---
name: skill-review
description: 8维评分框架审查 Hermes/Claude Code 技能质量。支持 GitHub 仓库 URL 或本地路径，输。Claude 专属增强版见 claude-skill-auditor 仓库（全英文、加权评分、S/A/B/C/D/F评级）。出终端评分摘要 + HTML 详细报告。
tags: [review, audit, skill-quality, code-review, hermes, claude-code, analysis]
---

# Skill Review Tool

一道专业的 Hermes / Claude Code 技能审查工具。

## 功能

- **8 维评分**：从代码质量、文档完整性、架构设计、用户体验、错误处理、跨平台兼容、可维护性、创新价值 8 个维度打分
- **双模式**：支持 GitHub 仓库 URL 远程审查 + 本地目录审查
- **双输出**：终端即时评分摘要 + HTML 详细报告（含柱状图、评级、改进建议）
- **零依赖**：纯 Python 标准库，无需 pip install

## 使用方法

```bash
# 审查 GitHub 仓库上的 skill
python review_tool.py https://github.com/lamwon/hermes-image-generation-skill

# 审查并生成 HTML 报告
python review_tool.py https://github.com/lamwon/hermes-image-generation-skill --html

# 指定报告输出路径
python review_tool.py https://github.com/xxx/skill-name --html -o my-report.html

# 审查本地目录
python review_tool.py /path/to/skill/folder --html
```

## 输出示例

```
==================================================
  SKILL REVIEW REPORT
  lamwon/hermes-image-generation-skill
==================================================

  代码质量     [####------] 4.0/10
  文档完整性    [#########-] 9.0/10
  架构设计     [#######---] 7.0/10
  用户体验     [#######---] 7.5/10
  错误处理     [########--] 8.0/10
  跨平台兼容    [#######---] 7.0/10
  可维护性     [######----] 6.5/10
  创新与价值    [#######---] 7.0/10

  >>> 总分: 7.0/10  评级: B <<<

  改进建议:
    1. 增加 try/except 错误处理，避免直接崩溃
    2. 添加 --help 参数和用法说明
    3. 使用 os.path.join 替代硬编码路径分隔符
    4. 配置项集中管理，方便修改
```

HTML 报告打开后为深色主题的完整评分页，包含仓库信息、文件结构、柱状图和具体建议。

## 8 维评分框架

| 维度 | 权重 | 考察内容 |
|------|------|---------|
| 代码质量 | 1.0x | 语法正确性、错误处理、安全性、代码风格 |
| 文档完整性 | 1.0x | README 是否完整、有安装/使用/FAQ |
| 架构设计 | 0.8x | 文件结构、依赖管理、工程化配置 |
| 用户体验 | 0.9x | 安装简便性、参数直观度、中文友好 |
| 错误处理 | 0.8x | 网络重试、限流处理、边缘情况 |
| 跨平台兼容 | 0.6x | Windows/Mac/Linux、路径编码 |
| 可维护性 | 0.6x | 注释、配置集中、版本管理 |
| 创新价值 | 0.5x | 差异化、真实痛点、对比表 |

## Pitfalls

1. GitHub API 有频率限制（未认证 60次/小时），频繁审查请使用 token
2. 审查结果仅供参考，不能替代人工审查
3. 对于大型仓库，只审查关键文件（SKILL.md / README.md / .py 文件）
4. 本地审查模式需要提供正确的文件路径

## 验证

```bash
python review_tool.py https://github.com/lamwon/hermes-image-generation-skill --html
# 应输出 8 维评分摘要并生成 HTML 文件
```
