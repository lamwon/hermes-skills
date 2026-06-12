---
name: windows-gui-pyside6-setup
description: Build PySide6 desktop GUI apps alongside Hermes Agent on Windows. Covers embedded Python env var conflicts, clean venv setup, multi-session QThread architecture, and deployment patterns. Use when user wants a desktop GUI for Hermes or any PySide6 application on Windows with embedded/portable Python.
version: 1.0.0
author: Hermes Agent
tags: [windows, pyside6, gui, embedded-python, pip-conflict, venv, qthread, multi-session]
related_skills: [artstyle-ai-framework, hermes-agent-setup, claude-code]
---

# Windows GUI (PySide6) Development with Hermes Agent

## Critical Environment Discovery

**The conflicting env vars (PIP_PREFIX, PIP_TARGET, PYTHONPATH) are set GLOBALLY by Hermes** — they aren't just in the terminal, they're in the OS environment. The `pip config list` shows `:env:.prefix` and `:env:.target` which means they come from environment variables, not config files. This means:

- Every `pip install` command will fail for native-extension packages unless env vars are cleared
- Every `python main.py` invocation will have a polluted `sys.path` unless env vars are cleared
- The `execute_code` sandbox inherits these vars too, but uses a different Python binary

**Key debugging technique**: Check env vars with:
```
cmd //c "set PIP"     # Shows PIP_PREFIX and PIP_TARGET
cmd //c "set PYTHON"  # Shows PYTHONPATH
```

**The Hermes sandbox vs terminal split**: `execute_code` tool runs under `D:\\Hermes\\portable-hermes-agent\\python_embedded\\python.exe` while terminal (Git Bash) resolves `python3` to the WindowsApps shim or WorkBuddy Python. ALWAYS use the full venv path in terminal commands:
```
# WRONG — may resolve to wrong Python:
cd /d/project && python main.py

# RIGHT — explicit path:
D:/project/venv/Scripts/python.exe main.py
```

## The Core Problem

Hermes Agent on Windows often uses an **embedded/portable Python distribution** (e.g. `python_embedded/`). This environment has:

1. **Env vars baked in**: `PIP_PREFIX` and `PIP_TARGET` point to the embedded Python's `site-packages`, causing pip to fail with `ERROR: Cannot set --home and --prefix together` when installing packages with native extensions (like PySide6).
2. **PYTHONPATH interference**: `PYTHONPATH` may point to the embedded Python's `site-packages`, causing version conflicts when a venv Python tries to load the embedded Python's packages (e.g. Python 3.13 PIL loaded into Python 3.11).
3. **No GUI support**: Embedded Python distributions lack Tcl/Tk and other GUI infrastructure. PySide6 requires a full Python installation.

## Step-by-Step: Setting Up PySide6

### 1. Find a Full System Python

```bash
# Look in standard locations
ls /c/Users/*/AppData/Local/Programs/Python/ 2>/dev/null
# Or check PATH
cmd //c "where python"
```

Target a full Python (not embedded): `C:\Users\<user>\AppData\Local\Programs\Python\Python311\python.exe`

### 2. Create a Clean Virtual Environment

```bash
# CRITICAL: Clear all conflicting env vars before running ANY python/pip command
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" \
  "C:\Users\<user>\AppData\Local\Programs\Python\Python311\python.exe" \
  -m venv D:\path\to\your-project\venv
```

### 3. Install Dependencies (always with env vars cleared)

```bash
cd /d/path/to/your-project && \
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" \
  venv/Scripts/pip.exe install PySide6 Pygments markdown pyyaml httpx pillow
```

### 4. Create a Launch Wrapper (start.bat)

Always include this to ensure env vars don't interfere at runtime:

```batch
@echo off
cd /d D:\path\to\your-project
set PIP_PREFIX=
set PIP_TARGET=
set PYTHONPATH=
echo Starting app...
.\venv\Scripts\python.exe main.py
pause
```

### 5. Check Python/Runtime Discrepancy

Hermes Agent's `execute_code` sandbox uses the **embedded Python** (e.g. `D:\Hermes\portable-hermes-agent\python_embedded\python.exe`), while the terminal may use a different Python. Always verify with:

```bash
which python3 && python3 -c "import sys; print(sys.executable)"
```

If they differ, use the full venv path explicitly in all terminal commands.

## Dark Theme QSS Pattern

Windows users often find white backgrounds blinding. Default to dark theme. The key pattern is a **centralized QSS stylesheet** with a toggle method:

```python
# theme.py — centralized, NOT inline
DARK_THEME = """
QMainWindow { background: #1e1e1e; }
QWidget { background: #1e1e1e; color: #d4d4d4; font-size: 13px; }

QTabWidget::pane { background: #252526; border: 1px solid #3c3c3c; }
QTabBar::tab {
    background: #2d2d2d; color: #999; padding: 8px 20px;
    border: 1px solid #3c3c3c; border-radius: 4px 4px 0 0;
    font-size: 13px;
}
QTabBar::tab:selected { background: #1e1e1e; color: #fff; border-bottom: 2px solid #4fc3f7; }
"""
```

### Message bubble styling for dark backgrounds

Chat messages need inline HTML since they're inside QTextBrowser (QSS doesn't apply to HTML content):

```python
# Dark theme message colors
if role == "user":
    bg, border, text_color = "#2b3a4a", "#3a5a7a", "#e0e0e0"
elif role == "assistant":
    bg, border, text_color = "#2d2d2d", "#404040", "#d4d4d4"
else:  # system
    bg, border, text_color = "#3a3a2a", "#5a5a3a", "#d4d4c0"

html = f'''
<div style="background:{bg}; border-radius:10px; padding:14px 18px;
            margin:10px 0; border:1px solid {border}; color:{text_color};
            font-size:15px; line-height:1.7;">
    <div style="color:#888; font-size:13px; margin-bottom:6px;">{icon} {label}</div>
    <div>{md_html}</div>
</div>
'''
```

### Theme toggle in MainWindow

```python
def _apply_theme(self):
    self.setStyleSheet(DARK_THEME if self._dark_mode else LIGHT_THEME)

def _toggle_theme(self):
    self._dark_mode = not self._dark_mode
    self._apply_theme()
```

Bind to `Ctrl+,` for quick toggle.

### Font sizes for readability on high-DPI Windows

| Element | Default Size | Dark Theme Size |
|---------|-------------|-----------------|
| Base UI | 10px | 13px |
| Chat messages | 12px | 15px |
| Input area | 12px | 15px |
| Buttons | 10px | 14px |
| Tab labels | 10px | 13px |
| Status bar | 10px | 13px |

## Verifying Dependencies

Create a `check_deps.py`:

```python
"""Verify all GUI dependencies are installed."""
import subprocess, os
checks = [
    ("PySide6.QtWidgets", "QApplication"),
    ("PIL", "Image"),
    ("markdown", None),
    ("yaml", None),
    ("httpx", None),
]
for mod, attr in checks:
    try:
        m = __import__(mod, fromlist=[attr] if attr else [])
        if attr: getattr(m, attr)
        print(f"  {mod}: OK")
    except Exception as e:
        print(f"  {mod}: FAIL - {e}")
```

Run it with env vars cleared:

```bash
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" \
  D:/path/to/venv/Scripts/python.exe check_deps.py
```

## CRITICAL: Streaming Response Display Bug

**The #1 mistake: storing chunks in a buffer but never writing them to the screen.**

```python
# WRONG — user sees nothing
def _on_message_chunk(self, session_id, content):
    self._assistant_buffers[session_id] += content  # stored but NOT displayed!

# RIGHT — display every chunk
def _on_message_chunk(self, session_id, content):
    tab = self._get_tab(session_id)
    buffer = self._assistant_buffers.get(session_id, "")
    if not buffer:
        tab.display.append_message("assistant", "")  # create placeholder
    self._assistant_buffers[session_id] = buffer + content
    tab.display.append_chunk(content)  # ★ MUST write to screen
```

### append_chunk: cursor-to-end pattern

Use `insertPlainText` (NOT `insertHtml`) for streaming chunks — QTextBrowser's `insertHtml` inserts at cursor position which may not be at the end:

```python
def append_chunk(self, content):
    cursor = self.textCursor()
    cursor.movePosition(cursor.End)
    self.setTextCursor(cursor)
    self.insertPlainText(content)  # always appends at bottom
    self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
```

### Thinking indicator pattern

Signal the session status through the session manager chain:

```python
# Session.send_message()
self.status = "waiting"
self.status_changed.emit(self.id, "waiting")

# SessionManager.create_session()
session.status_changed.connect(
    lambda sid, st: self.session_status.emit(sid, st)
)

# In MainWindow
def _on_session_status(self, session_id, status):
    tab = self._get_tab(session_id)
    if status == "waiting":
        tab.thinking_label.setText("  思考中...")
        tab.thinking_label.show()
    elif status == "idle":
        tab.thinking_label.hide()
    elif status == "error":
        tab.thinking_label.setText("  出错了")
        tab.thinking_label.setStyleSheet("color: #ff5252;")
```

## Enter-to-Send, Shift+Enter-Newline

**Default QPlainTextEdit behavior**: Enter = newline. Users expect Enter = send.

Solution: subclass QPlainTextEdit:

```python
class SendEdit(QPlainTextEdit):
    send_pressed = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)    # Shift+Enter = newline
            else:
                self.send_pressed.emit()        # Enter = send
        else:
            super().keyPressEvent(event)
```

## Multi-Session QThread Architecture

For a chat GUI with multiple parallel conversations, use this pattern:

```
MainWindow (QMainWindow)
  ├── QTabWidget (one tab per session)
  │     └── ChatTab (per tab)
  │           ├── ChatDisplay (QTextBrowser + Markdown)
  │           └── InputPanel (QPlainTextEdit + drag-drop)
  ├── SessionManager (QObject)
  │     └── Session (QObject, per session)
  │           └── ChatWorker (QThread, per API call)
  ├── FileHandler (drag-drop file reading)
  ├── ClipboardManager (QClipboard wrapper)
  └── SettingsDialog (LLM provider config)
```

### Key Pattern: QThread Isolation

Each tab gets its own `AIAgent`-equivalent and `QThread`:

```python
class ChatWorker(QThread):
    chunk_received = Signal(str)
    finished = Signal()

    def __init__(self, client, messages):
        super().__init__()
        self.client = client
        self.messages = messages
        self._is_interrupted = False

    def run(self):
        for chunk in self.client.chat_stream(self.messages):
            if self._is_interrupted:
                return
            self.chunk_received.emit(chunk)
        self.finished.emit()

class Session(QObject):
    message_received = Signal(str, str)  # session_id, content
    def send_message(self, text):
        self._worker = ChatWorker(self._client, self.messages)
        self._worker.chunk_received.connect(
            lambda c: self.message_received.emit(self.id, c)
        )
        self._worker.start()  # Non-blocking!
```

### Thread Safety Rules
- Never update UI from worker thread directly
- Use Qt Signals/Slots for all cross-thread communication
- Each Session holds its own message list (no shared mutable state)
- Use `QMutex` guards if sessions share resources

## LLM Client Pattern

Multi-provider abstraction that works with streamed responses:

```python
class LLMClient:
    def chat_stream(self, messages):
        cfg = self._get_cfg()
        with httpx.Client(timeout=cfg.timeout) as client:
            resp = client.post(f"{cfg.base_url}/chat/completions", ...)
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    chunk = json.loads(line[6:])
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content
```

Supports DeepSeek, OpenAI, Anthropic, and any OpenAI-compatible API.

## File Handler Pattern

Drag-drop support with text file reading and image preview:

```python
def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()

def dropEvent(self, event):
    files = [u.toLocalFile() for u in event.mimeData().urls()]
    self.process_files(files)
```

Smart encoding detection for Chinese Windows environments:
```python
encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
for enc in encodings:
    try:
        return path.read_text(encoding=enc)
    except UnicodeDecodeError:
        continue
```

## Settings Dialog Pattern

Runtime-switchable LLM providers with connection testing:

```python
class SettingsDialog(QDialog):
    # QTabWidget, one tab per provider
    # Each tab: API Key, Base URL, Model, Timeout
    # Test Connection button -> httpx.post() with 10s timeout
    # Save -> config.yaml
```

## Launch Method Matters

**DO NOT run from inside the Hermes terminal** — the conflicting env vars will corrupt the GUI. Instead:

1. **Double-click `start.bat`** in Explorer (recommended):
```batch
@echo off
cd /d D:\path\to\project
set PIP_PREFIX=
set PIP_TARGET=
set PYTHONPATH=
start "ArtStyle AI" .\venv\Scripts\python.exe main.py
```

2. **Or from a fresh cmd window** (Win+R → cmd):
```
D:
cd D:\path\to\project
set PIP_PREFIX=
set PIP_TARGET=
set PYTHONPATH=
.\venv\Scripts\python.exe main.py
```

## Session Persistence Pattern

Save/load conversation sessions as JSON:

```python
# Save
def _save_session(self):
    data = session.to_dict()  # id, name, model, messages, created_at
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Session.to_dict()
def to_dict(self):
    return {
        "id": self.id, "name": self.name,
        "model": self.model, "provider": self.provider,
        "messages": self.messages,
        "created_at": self.created_at.isoformat(),
    }
```

Each session stores its own message list — independent context per tab. This enables:
- Restoring conversations on app restart
- Exporting individual conversations
- Searching across all saved sessions

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `pip install` fails with `--home and --prefix` | PIP_PREFIX + PIP_TARGET env vars | `PIP_PREFIX="" PIP_TARGET="" pip install ...` |
| Import loads wrong version | PYTHONPATH pointing to embedded Python | `PYTHONPATH="" python ...` or use start.bat wrapper |
| `No module named 'PySide6'` even after install | Installed to wrong Python | Use full venv path, clear env vars |
| `_imaging` C extension fails | Version mismatch (py3.13 .pyd loaded into py3.11) | Clear PYTHONPATH, reinstall into venv |
| GUI won't start | Embedded Python can't run PySide6 | Use full system Python + clean venv |
| Chinese text garbled | Terminal encoding mismatch | Use `Microsoft YaHei` font, UTF-8 files |

## Project Template Structure

```
project/
├── main.py               # Entry point
├── start.bat             # Launch wrapper (clears env vars)
├── main_window.py        # QMainWindow + QTabWidget
├── chat_tab.py           # ChatTab (display + input + drag-drop)
├── session_manager.py    # SessionManager + QThread workers
├── file_handler.py       # File drag-drop + reading
├── clipboard_manager.py  # QClipboard wrapper
├── settings_dialog.py    # LLM provider config
├── llm_client.py         # Multi-provider API client
├── config.yaml           # Provider configuration
├── check_deps.py         # Dependency verification
└── venv/                 # Virtual environment (from system Python)
```
