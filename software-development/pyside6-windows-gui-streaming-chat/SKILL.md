---
name: pyside6-windows-gui-streaming-chat
description: Build a PySide6 desktop chat GUI on Windows with streaming LLM responses, multi-tab sessions, file drag-drop, and cyberpunk neon theme. Covers Python environment setup, QTimer polling for cross-thread streaming, Enter-to-send, and dark theme QSS.
version: 1.0.0
author: Hermes Agent
tags: [pyside6, qt6, gui, chat, streaming, windows, cyberpunk, multi-thread]
related_skills: [artstyle-ai-framework, claude-code, systematic-debugging]
---

# PySide6 Windows GUI Streaming Chat

Building a desktop chat interface with streaming LLM responses on Windows requires navigating several pitfalls. This skill captures the working architecture.

## Architecture: QTimer Polling (NOT Signal Chains)

Qt signals across QThread boundaries **silently fail** when lambdas are connected without explicit `Qt.QueuedConnection`. Even with QueuedConnection, complex signal chains are fragile. 

**Use QTimer polling instead:**

```
Worker Thread (QThread)
    └─ writes to shared deque (thread-safe by GIL for simple append/pop)
        
Main Thread (QTimer 50ms)
    └─ polls all sessions' deques every 50ms
    └─ displays chunks to QTextBrowser
    └─ NO signal connections across threads
```

### Key Files Structure

```
project/
├── main.py              # Entry: QApplication + MainWindow
├── main_window.py       # MainWindow + QTimer + tab management + polling
├── chat_tab.py          # ChatDisplay + SendEdit(Enter=send) + InputPanel
├── session_manager.py   # Session + ChatWorker + thread-safe deque
├── file_handler.py      # File drag-drop + reading with encoding detection
├── clipboard_manager.py # QClipboard integration
├── settings_dialog.py   # LLM provider config panel
├── llm_client.py        # HTTP streaming client (httpx)
├── theme.py             # Cyberpunk neon QSS
├── config.yaml          # Provider config
└── start.bat            # Launcher with env cleanup
```

## Critical Pattern: Streaming Display

```python
# session_manager.py - Worker writes to deque
class ChatWorker(QThread):
    def __init__(self, client, messages, chunks: deque):
        super().__init__()
        self.chunks = chunks  # shared deque
    
    def run(self):
        for chunk in self.client.chat_stream(self.messages):
            self.chunks.append(chunk)
        self.chunks.append("__DONE__")

# main_window.py - Timer polls deque
self._poll_timer = QTimer(self)
self._poll_timer.timeout.connect(self._poll_sessions)
self._poll_timer.start(50)  # 50ms polling interval

def _poll_sessions(self):
    for sid, session in self.sessions.items():
        chunks = session.get_pending(50)
        for chunk in chunks:
            if chunk == "__DONE__":
                # mark complete
            elif chunk.startswith("__ERROR__:"):
                # show error
            else:
                tab.display.append_chunk(chunk)
```

### Display Chunk at End of Document

```python
def append_chunk(self, text: str):
    """Append plain text at the very end."""
    from PySide6.QtGui import QTextCursor
    cursor = self.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    cursor.insertText(text)
    sb = self.verticalScrollBar()
    sb.setValue(sb.maximum())  # auto-scroll
```

**NOT** `self.insertPlainText(text)` — that inserts at cursor position.
**NOT** `self.append(html)` — that adds a QTextEdit block (wrong for streaming).
Use `QTextCursor.insertText()` at End.

## Python Environment on Windows

### The PIP_PREFIX / PIP_TARGET Problem
Hermes agent sets `PIP_PREFIX` and `PIP_TARGET` env vars pointing to the embedded Python at `portable-hermes-agent/python_embedded`. These cause:

1. `pip install PySide6` fails with "Cannot set --home and --prefix together"
2. When they do "succeed," packages get installed to the WRONG Python
3. Version conflicts: Python 3.13 embedded modules loaded into Python 3.11 venv

### Fix: Create a clean venv

```bash
# Use the SYSTEM Python (not embedded), not the Hermes .venv
"C:\Users\Windows\AppData\Local\Programs\Python\Python311\python.exe" -m venv D:\path\to\gui\venv

# Clear interfering env vars BEFORE installing
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" venv/Scripts/pip.exe install PySide6 ...

# Clear env vars BEFORE running too
set PIP_PREFIX=
set PIP_TARGET=
set PYTHONPATH=
.\venv\Scripts\python.exe main.py
```

### start.bat Template
```batch
@echo off
cd /d D:\path\to\gui
set PIP_PREFIX=
set PIP_TARGET=
set PYTHONPATH=
.\venv\Scripts\python.exe main.py
```

## Enter=Send / Shift+Enter=Newline

```python
class SendEdit(QPlainTextEdit):
    send_pressed = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)  # newline
            else:
                self.send_pressed.emit()       # send
        else:
            super().keyPressEvent(event)
```

## Cyberpunk Neon Theme (QSS)

| Element | Color | Hex |
|---------|-------|-----|
| Background | Near-black with blue tint | `#0a0a12` |
| Panel surface | Dark navy | `#0d0d1a` |
| Text primary | Soft white-blue | `#d0d0e8` |
| Text secondary | Muted purple | `#8888cc` |
| **Primary accent** | Cyan neon | `#00fff2` |
| **Secondary accent** | Magenta neon | `#ff00ff` |
| Border default | Dark border | `#2a2a5a` |
| Tab selected | Cyan top-glow | `border-top: 2px solid #00fff2` |
| Input focus | Cyan border | `border-color: #00fff2` |
| User message | Dark navy + left cyan edge | `border-left: 3px solid #00fff2` |
| AI message | Dark + left green edge | `border-left: 3px solid #00ff88` |

Use `setStyleSheet()` with the full QSS string. Toggle themes by swapping stylesheets.

## LLM Client API Key Resolution

Config may contain `${ENV_VAR}` placeholders. Resolve them before use:

```python
def _resolve_key(self, raw: str) -> str:
    if raw.startswith("${") and raw.endswith("}"):
        return os.getenv(raw[2:-1], "")
    return raw
```

## Multi-Tab Sessions

```python
class Session:
    def __init__(self):
        self.chunks = deque()  # thread-safe
        self.status = "idle"
        self.messages = []
        self._worker = None

    def send_message(self, text: str):
        self.chunks.clear()
        self._worker = ChatWorker(self._client, self.messages, self.chunks)
        self._worker.start()

    def get_pending(self, max_items=50):
        items = []
        while self.chunks and len(items) < max_items:
            items.append(self.chunks.popleft())
        return items
```

Each tab has its own Session with independent `chunks` deque. The QTimer polls ALL sessions' deques in every tick.

## Dependencies

```bash
pip install PySide6 Pygments markdown pyyaml python-dotenv httpx pillow
```

## Known QTextCursor.End Error

```pytb
AttributeError: 'PySide6.QtGui.QTextCursor' object has no attribute 'End'
```

**Fix:** Use `QTextCursor.MoveOperation.End` instead of bare `QTextCursor.End`:
```python
from PySide6.QtGui import QTextCursor
cursor = self.textCursor()
cursor.movePosition(QTextCursor.MoveOperation.End)  # NOT cursor.End
cursor.insertText(text)
```

## Copy/Paste Direction Bug

`QTextBrowser.textCursor().selectedText()` reads selected text FROM the display.
`QClipboard.setText()` writes TO the system clipboard.
These can be accidentally swapped — always verify direction:

```python
def copy_selected_to_clipboard(self):
    """✅ Read FROM display, write TO clipboard."""
    txt = self.display.textCursor().selectedText()
    if txt:
        QApplication.clipboard().setText(txt)

def paste_from_clipboard_to_input(self):
    """✅ Read FROM clipboard, write TO input."""
    text = QApplication.clipboard().text()
    if text:
        self.input_panel.input_edit.insertPlainText(text)
```

## Double-Emission Bug in Send Flow

When _on_send() emits the signal TWICE (once for files, once for text), the handler
gets called twice, duplicating the user message. Always emit once:

```python
# ❌ WRONG - double emit
def _on_send(self, text, files):
    if files:
        self.files_dropped.emit(files)
    self.files_dropped.emit([f"__TEXT__:{text}"])

# ✅ CORRECT - single emit with combined payload
def _on_send(self, text, files):
    parts = []
    if files:
        parts.extend(files)
    if text:
        parts.append(f"__TEXT__:{text}")
    if parts:
        self.files_dropped.emit(parts)
```

Then in the handler, split them:
```python
text_parts = [f for f in items if f.startswith("__TEXT__:")]
file_paths = [f for f in items if not f.startswith("__TEXT__:")]
```

## Pitfalls

1. **Qt signals across threads without `Qt.QueuedConnection`** → lambdas run in worker thread, UI updates silently swallowed. Use QTimer polling instead.
2. **`QTextCursor.End` is wrong** in PySide6 → use `QTextCursor.MoveOperation.End`
3. **`PIP_TARGET` env var** → prevents clean installs, must clear before pip install
4. **`PYTHONPATH` env var** → causes wrong module resolution, must clear before running
5. **Streaming API**: `client.post(..., stream=True)` with `resp.iter_lines()` — DeepSeek/OpenAI SSE format: `data: {"choices":[{"delta":{"content":"..."}}]}`
6. **QTextBrowser vs QTextEdit** for markdown: QTextBrowser supports `setHtml()` and `append(html)` but not rich editing. Use QTextBrowser for read-only chat display.
7. **`__DONE__` sentinel**: Worker writes a sentinel value so the timer knows stream is complete. Use a unique string that won't appear in normal text.
