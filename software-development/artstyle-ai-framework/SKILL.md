---
name: artstyle-ai-framework
description: 完整设计框架 for ArtStyle AI - 视觉设计大师 Windows 应用。八维闭环系统架构（指挥/协调/分工/保障/设计/监督/控制/验收）+ 22个Skill映射 + Hermes Agent + Claude Code 提示词方案。
version: 1.0.0
author: Hermes Agent
tags: [design-framework, architecture, artstyle-ai, visual-design, windows-app]
related_skills: [claude-code, writing-plans, subagent-driven-development, comfyui, excalidraw, dspy, instructor, test-driven-development, code-review]
---

# ArtStyle AI 视觉设计大师 — 完整设计框架

## 项目总览

**目标：** 开发一个单机安装的 Windows 平面视觉设计输出应用，整合主流设计风格与古今中外画家理念，通过 NLP/LLM 交互完成从概念到成品的设计闭环。

**核心能力矩阵：**
1. 设计风格库 — YAML 风格配置 + ComfyUI workflow 模板
2. 画家理念引擎 — LLM 推理风格参数 + LoRA 模型
3. NLP 自然语言输入 — DeepSeek / OpenAI / Anthropic 多模型
4. LLM 运行时配置 — config.yaml 动态加载
5. 提示词专家系统 — Hermes skill + 预置模板库
6. 单机安装 — NSIS/Inno Setup 打包

---

## 八维闭环系统架构

### 1. 指挥层 (Command)
- **职责：** 任务分解与分发、资源调度、优先级决策
- **实现：** Hermes Agent Orchestrator → delegate_task
- **组件：** Task Dispatcher, Resource Manager, Priority Scheduler
- **联动 Skill：** `subagent-driven-development`, `claude-code`, `writing-plans`, `plan`

### 2. 协调层 (Coordination)
- **职责：** 模块间通信、状态同步、冲突消解
- **组件：** Message Bus, State Manager (JSON schema + 版本号), Conflict Resolver
- **联动 Skill：** `dspy`, `excalidraw`, `writing-plans`

### 3. 分工层 (Division of Labor)
| Agent 角色 | 职责 | 联动 Skill |
|-----------|------|-----------|
| Style Agent | 设计风格选择与融合 | `comfyui`, `clip` |
| Painter Agent | 画家理念推理与应用 | — |
| NLP Agent | 自然语言解析与指令生成 | `instructor`, `outlines` |
| Prompt Agent | 提示词工程优化 | `guidance`, `dspy` |
| Code Agent | 功能代码实现 | `claude-code`, `codex` |
| Review Agent | 质量审核与验收 | `code-review` |

### 4. 保障层 (Support)
- Installer System: NSIS / Inno Setup 一键安装
- Config Manager: config.yaml + .env
- Logging System: JSON Lines 结构化日志
- Model Connector: DeepSeek / OpenAI / Anthropic / Ollama
- **联动 Skill：** `hermes-agent-setup`, `gguf-quantization`, `llama-cpp`

### 5. 设计层 (Design)
- Canvas Engine: Pillow/Cairo 2D 渲染管线
- Style Renderer: YAML 配置 → 参数化渲染
- Color System: HSL/LAB/孟塞尔色彩理论
- Composition Engine: 黄金分割、三分法
- Painter Inference: LLM 推理 → 渲染参数
- **联动 Skill：** `comfyui`, `clip`

### 6. 监督层 (Supervision)
- Style Consistency Check: 对比输出与目标风格偏差
- Design Principle Validator: 黄金比例、色彩和谐度、视觉平衡
- Output Validator: 分辨率、色域、文件格式
- **联动 Skill：** `code-review`, `test-driven-development`

### 7. 控制层 (Control)
- Workflow State Machine: enum 驱动状态图
- Version Control: git 标签追踪设计版本
- Rollback Manager: 版本历史 + 回滚 API
- **联动 Skill：** `systematic-debugging`, `subagent-driven-development`

### 8. 验收层 (Acceptance)
- Output Generator: PNG / SVG / PDF / PSD 多格式导出
- Quality Report: 自动生成设计评审报告
- Feedback Loop: 用户反馈 → 风格库/提示词库迭代
- **联动 Skill：** `requesting-code-review`, `nano-pdf`, `powerpoint`, `ocr-and-documents`

---

## Orchestrator 主循环（伪代码）

```
1. 加载项目上下文 + 22 个 Skill
2. 用户需求 → delegate_task(writing-plans) → 实施计划
3. 对每个 Task:
   a. delegate_task(实施) + TDD
   b. delegate_task(规范审核)
   c. delegate_task(质量审核)
   d. 审核通过 → 标记完成；不通过 → dispatch_fix
4. 集成验收 → delegate_task(requesting-code-review)
```

### 核心原则
- 每个 Task ≤ 5 分钟，修改 ≤ 3 个文件
- 必须先写测试（TDD）
- 子 Agent 无记忆 — 每次 delegate_task 附带完整上下文
- 审核不通过必须修复再审
- 所有中间产物保存到文件系统

---

## Hermes Agent 提示词模板

### 系统提示词（Orchestrator 入口）
```
你正在主导开发 "ArtStyle AI - 视觉设计大师" Windows 应用程序。

## 你的身份
你是本项目总指挥官 (Orchestrator)，负责指挥、协调、分工、保障、设计、监督、控制、验收八个环节的闭环。

## 核心原则
1. 每一次 delegate_task 必须附带完整的上下文
2. 每个功能实现必须经过"实施→规范审核→质量审核"三阶段
3. Task 粒度控制在 2-5 分钟可完成，不超过 3 个文件修改
4. 优先使用现有的 Hermes Skill 而非重新发明轮子
5. 设计相关任务优先使用 comfyui 管线方案

## 可用的 Skill 清单
${skill_list}

## 当前任务优先级
${priority_list}
```

### 需求解析 → 结构化 JSON
```json
{
  "design_type": "海报/Logo/UI/插画",
  "target_style": ["极简", "赛博朋克", "水墨风"],
  "painter_influence": ["范宽", "莫奈", "葛饰北斋"],
  "color_preference": "暖色调/冷色调/黑白",
  "llm_config": {"provider": "deepseek", "model": "deepseek-v4-flash"},
  "output_format": "PNG/SVG/PDF"
}
```

---

## Claude Code 提示词模板

### 标准调用格式
```
terminal(command="claude '<TASK_DESCRIPTION>'",
         workdir="<PROJECT_ROOT>",
         pty=true, background=true)
```

### 项目启动提示词
```
You are now a coding agent for the "ArtStyle AI - Visual Design Master" project.
Technology Stack: Python 3.11+, Pillow/Cairo, ComfyUI, httpx, Pydantic, PyTest
Development Principles: TDD, PEP 8, type hints, modular design, structured logging
```

### 核心模块提示词（示例：Canvas 引擎）
```
Implement src/engine/canvas.py:
- Canvas class: width, height, dpi, add_layer(), render(), export(), resize()
- Layer class: draw_rect(), draw_circle(), draw_text(), set_blend_mode(), set_opacity()
- Use Pillow ImageDraw + ImageFilter
- TDD: write tests first in tests/engine/test_canvas.py
```

---

## 项目目录结构
```
artstyle-ai/
├── src/
│   ├── main.py                  # 应用入口
│   ├── engine/                  # 核心设计引擎
│   │   ├── canvas.py            # Canvas 渲染
│   │   ├── styles.py            # 风格注册+融合
│   │   ├── styles/              # 风格YAML配置
│   │   ├── colors.py            # 色彩理论
│   │   ├── composition.py       # 构图规则
│   │   └── painters.py          # 画家推理
│   ├── llm/                     # LLM 集成
│   │   ├── connector.py         # DeepSeek/OpenAI/Anthropic/Ollama
│   │   ├── optimizer.py         # 提示词优化
│   │   └── templates/           # 提示词模板
│   ├── pipeline/                # 图像生成管线
│   │   ├── workflow.py          # ComfyUI workflow
│   │   └── renderer.py          # 输出渲染
│   ├── config/                  # 配置系统
│   │   ├── settings.py          # 配置加载/保存
│   │   └── default.yaml
│   └── cli/                     # CLI 界面
│       ├── commands.py
│       └── ui.py
├── tests/                       # 测试套件
├── installer/                   # NSIS/Inno Setup 打包
│   ├── setup.iss / setup.nsi
│   └── build.py
├── config.yaml
├── .env.example
└── requirements.txt
```

---

---

## GUI 桌面前端架构

**技术栈: PySide6 (Qt for Python)** — 原生 Windows 外观，完整控件生态。

### 三大核心能力

| 能力 | 实现 | 用户操作 |
|------|------|---------|
| 对话框 复制粘贴 | QTextBrowser(Markdown渲染) + QClipboard API | Ctrl+C 选中复制，Ctrl+V 粘贴文本/图片 |
| 阅读文件 | FileHandler: 拖拽(QDragEnterEvent) + 文件选择(QFileDialog) | 拖拽文件到输入框，或 Ctrl+O 选择文件 |
| 多对话并行 | QTabWidget + SessionManager + QThread 每Tab独立Agent | Ctrl+T 新建Tab，Ctrl+Tab 切换，互不中断 |

### 架构层级

```
用户(键盘/鼠标/剪贴板/文件)
    ↓
GUI 前端层 (PySide6 Desktop)
├── MainWindow (QMainWindow)
│   ├── MenuBar: File | Edit | Session | Settings | Help
│   ├── Toolbar: [+新Tab] [📂打开文件] [📋复制] [🗑清空] [⚙设置]
│   ├── Central: QTabWidget (每个Tab = 独立ChatTab)
│   │   └── ChatTab (QWidget)
│   │       ├── ChatDisplay (QTextBrowser + Markdown + Pygments)
│   │       ├── FilePreviewPanel (拖拽文件预览，可折叠)
│   │       └── InputPanel (QPlainTextEdit + 发送按钮 + 模型选择)
│   └── StatusBar: Tab数 | 当前模型 | 连接状态
│
├── SessionManager — 多会话管理器
│   ├── sessions: dict[str, AIAgent] — 每Tab独立Agent实例
│   ├── QThread 隔离 — API 调用不阻塞 UI
│   ├── 信号/槽 — 线程安全更新 UI
│   └── 会话持久化 — 关闭自动保存，启动恢复
│
├── FileHandler — 文件读写系统
│   ├── 拖拽: QDragEnterEvent → QDropEvent
│   ├── 选择: QFileDialog (支持多选)
│   ├── 支持: .txt/.md/.py/.json/.yaml/.png/.jpg/.svg
│   ├── 智能编码检测: UTF-8 → GBK → GB2312
│   └── 文件过大保护: >1MB 截断提示
│
└── ClipboardManager — 剪贴板集成
    ├── 复制: Ctrl+C (选中文本), Ctrl+Shift+C (代码块), 右键复制图片
    └── 粘贴: Ctrl+V (文本/图片), Ctrl+Shift+V (文件路径解析)
```

### 多会话并行核心设计

```python
class ChatWorker(QThread):
    """每个 Tab 的独立工作线程"""
    chunk_received = Signal(str)
    finished = Signal(str)
    
    def run(self):
        for chunk in self.agent.chat_stream(message):
            if self.isInterruptionRequested():
                return
            self.chunk_received.emit(chunk)

class SessionManager:
    sessions: dict[str, AIAgentSession]
    
    def create_session(self, model, provider) -> str:
        agent = AIAgent(model=model, ...)
        return session.id
    
    def send_message(self, session_id, message):
        worker = ChatWorker(self.sessions[session_id].agent, message)
        worker.chunk_received.connect(lambda c: ui.append_chunk(c))
        worker.start()  # 不阻塞！
```

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+Enter | 发送消息 |
| Ctrl+T | 新建 Tab |
| Ctrl+W | 关闭 Tab |
| Ctrl+Tab / Ctrl+1~9 | 切换 Tab |
| Ctrl+O | 打开文件 |
| Ctrl+S | 保存会话 |
| Ctrl+F | 搜索对话 |
| Ctrl+L | 清空对话 |
| Escape | 取消 API 调用 |
| F2 | 重命名 Tab |

### 设置面板

LLM 提供者配置（运行时切换 DeepSeek / OpenAI / Anthropic / Ollama）：
- API Key 管理（掩码显示 + 明文切换）
- Base URL 自定义
- Model 选择下拉
- 连接测试（显示延迟）
- 自定义提供者添加

### GUI 依赖安装

```bash
pip install PySide6 Pygments markdown pyyaml python-dotenv httpx pillow
```

---

## 22 个 Skill 速查表

| Skill | 用途 | 所属闭环 | 调用方式 |
|-------|------|---------|---------|
| claude-code | 核心功能代码实现 | 分工 | terminal(pty=true) |
| codex | 备选代码生成 | 分工 | terminal(pty=true) |
| subagent-driven-development | 子 Agent 驱动开发 | 指挥/控制 | delegate_task 循环 |
| writing-plans | 编写实施计划 | 指挥/协调 | read_file + write_file |
| test-driven-development | TDD 测试驱动 | 监督 | delegate_task 子 Agent |
| code-review | 代码质量审查 | 监督/验收 | delegate_task 子 Agent |
| requesting-code-review | 最终评审 | 验收 | 自动流程触发 |
| systematic-debugging | 系统性排错 | 控制 | delegate_task 子 Agent |
| comfyui | 图像生成管线 | 设计 | comfyui_generate / API |
| clip | 图像风格分析 | 设计/监督 | Python CLIP 调用 |
| excalidraw | 架构图/流程图 | 协调 | write_file .excalidraw |
| dspy | AI 系统声明式编程 | 协调/设计 | Python DSPy 模块 |
| instructor | 结构化 JSON 输出 | 分工 | @instructor 装饰器 |
| outlines | 生成格式保证 | 分工 | Python outlines |
| guidance | 控制 LLM 输出流 | 分工 | Python guidance |
| hermes-agent-setup | 安装配置辅助 | 保障 | hermes setup |
| gguf-quantization | 量化模型支持 | 保障 | llama-cpp 加载 |
| llama-cpp | 本地模型推理 | 保障 | Python llama-cpp-python |
| plan | 计划模式（不执行） | 指挥 | skill_view + write_file |
| nano-pdf | PDF 文档输出 | 验收 | nano-pdf CLI |
| powerpoint | PPTX 演示文稿输出 | 验收 | python-pptx 库 |
| ocr-and-documents | 文档文本提取 | 验收 | pymupdf / marker-pdf |
