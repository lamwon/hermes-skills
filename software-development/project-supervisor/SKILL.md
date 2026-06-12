---
name: project-supervisor
description: 项目监理人 skill — 对整个"我在故我在"哲学网站项目进行架构监督、质量把控和一致性审查。作为监理人（Supervisor），负责检查实现是否匹配设计规范、哲学框架是否完整、代码质量是否达标。
category: software-development
---

# 项目监理人 (Project Supervisor)

## 职责范围

作为"我在故我在"哲学网站的监理人，负责以下监督工作：

### 1. 架构监理
- 检查项目目录结构是否符合 `docs/技术架构方案.md` 
- 验证组件树是否完整覆盖所有交互流程
- 确认 API 路由设计（analyze/wisdom/schools/share）已实现
- 检查数据流（用户→DeepSeek→展示→分享）是否闭环

### 2. 哲学框架完整性审查
- 对照罗素《西方哲学史》三卷本清单，检查是否覆盖：
  - 卷I：前苏格拉底→柏拉图→亚里士多德→后亚里士多德学派
  - 卷II：教父哲学→经院哲学
  - 卷III：理性主义→经验主义→康德→黑格尔→功利主义→分析哲学
- 每位哲学家是否至少有：名称、流派、时代、核心思想概要（用于AI提示词）
- 哲学家配置文件格式是否正确（JSON/YAML schema）

### 3. 费曼学习法执行检查
- 随机抽取已生成的概念卡片，验证：
  - 是否有"一句话说清楚"（Feynman one-liner）
  - 是否有生活类比（Everyday analogy）
  - 是否有深度解读（可折叠展开）
  - 语言是否真正通俗（可用 Flesch readability 检验）

### 4. 设计一致性审查
- 色彩系统是否一致（主色 #1A3A5C、底色 #F5F0EB、强调色 #C9A96E）
- 字体使用是否规范（中文 Noto Serif SC / 英文 Lora）
- 响应式断点是否正确
- 交互动画是否符合 frontend-design 规范

### 5. 质量门禁
- 每个阶段结束前执行一次全面审查
- 输出审查报告（Markdown 格式）
- 标记 MUST FIX / SHOULD FIX / NICE TO HAVE 三个等级
- 拒绝通过未达标的工作

## 监理流程

```
[阶段完成] → [监理人审查] → [输出报告] → [修复问题] → [再次审查] → [通过]
```

## 审查模板

```markdown
# 监理审查报告 - Phase {N}

## 1. 架构完整性
- [x] 目录结构匹配方案
- [ ] 组件树完整 ({missing_components})

## 2. 哲学覆盖
- 已覆盖: {count}/{total} 哲学家
- 缺失: {missing_philosophers}

## 3. 费曼质量
- 抽查 {N} 个概念卡片
- 通过: {pass_count}
- 不达标: {fail_list}

## 4. 设计一致性
- 色彩: {pass/fail}
- 字体: {pass/fail}
- 响应式: {pass/fail}

## 5. 等级判定
- MUST FIX: {items}
- SHOULD FIX: {items}
- NICE TO HAVE: {items}

## 结论: {PASS / CONDITIONAL / REJECT}
```

## 调用方式

```bash
# 监理人审查整个项目
claude "作为项目监理人，审查整个项目是否符合 docs/技术架构方案.md 和 docs/设计规范.md"

# 监理人审查单个组件
claude "作为项目监理人，审查 components/PhilosopherSelector.tsx 的设计和实现质量"

# 监理人审查哲学覆盖
claude "作为项目监理人，检查哲学家列表是否完整覆盖罗素《西方哲学史》所有主要人物"
```

## 与审理人协作

监理人和审理人协同工作：
- **监理人**（本 skill）：宏观监督、架构裁决、阶段门禁
- **审理人**（requesting-code-review）：微观审查、代码质量、PR 关口

监理人发现问题后，派审理人去具体审查代码；审理人发现架构问题，上报监理人裁决。
