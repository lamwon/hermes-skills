---
name: pyside6-windows-gui-debug
description: "Debug patterns for PySide6 GUI apps on Windows alongside Hermes Agent. Covers: cross-thread signal failures, env var contamination from embedded Python, dark theme defaults, Enter-Send key handling, and dependency installation pitfalls."
version: 1.0.0
tags: [pyside6, qt, windows, gui, debugging, threading]
---

# PySide6 Windows GUI Debug Patterns

## The Core Problem: Env Var Contamination

Hermes Agent on Windows sets `PIP_PREFIX` and `PIP_TARGET` environment variables pointing to the embedded Python (`portable-hermes-agent/python_embedded/`). These env vars **leak into all child processes**, including virtual environments.

This causes:

1. **pip installs go to the wrong place** — `pip install PySide6` appears to succeed but installs into the embedded Python's site-packages, not the venv
2. **Import resolution chaos** — `PYTHONPATH` also points to embedded Python. Even from inside a clean venv, `from PIL import Image` loads the Python 3.13 embedded version into a Python 3.11 process, causing cryptic crashes

### Fix: Clear env vars before EVERY operation

```bash
# When installing
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" venv/Scripts/pip.exe install PySide6

# When running
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" venv/Scripts/python.exe main.py

# Better: wrap in a .bat file
@echo off
set PIP_PREFIX=
set PIP_TARGET=
set PYTHONPATH=
.\venv\Scripts\python.exe main.py
```

Or create a clean venv (the most reliable approach):

```python
import subprocess, os
env = os.environ.copy()
env.pop("PIP_PREFIX", None)
env.pop("PIP_TARGET", None)
env.pop("PYTHONPATH", None)
PY = r"C:\Users\Windows\AppData\Local\Programs\Python\Python311\python.exe"

# Create venv with clean env
subprocess.run([PY, "-m", "venv", "venv"], env=env)

# Install deps with clean env
PIP = "venv/Scripts/pip.exe"
for pkg in ["PySide6", "Pygments", "markdown", "pyyaml", "pillow"]:
    subprocess.run([PIP, "install", pkg], env=env)
```

---

## The Silent Bug: Cross-Thread Qt Signals

**This is the most dangerous Qt bug.** It silently fails — no errors, no warnings, the chunks arrive at the slot but the UI never updates.

### Root Cause

When a `QThread` emits a signal connected to a **lambda** without an explicit connection type, Qt uses `DirectConnection`. The lambda runs in the **worker thread**. Qt silently discards UI updates from non-main threads.

```python
# BAD — runs in WORKER thread, UI never updates
self._worker.chunk_received.connect(
    lambda c: self.message_received.emit(self.id, c)
)

# GOOD — runs in MAIN thread, UI updates correctly
self._worker.chunk_received.connect(
    lambda c: self.message_received.emit(self.id, c),
    Qt.QueuedConnection     # <- THIS IS CRITICAL
)
```

### The Rule

**Every signal connection from a QThread to any QObject must use `Qt.QueuedConnection`.**

```python
from PySide6.QtCore import QObject, Signal, QThread, Qt

class ChatWorker(QThread):
    chunk_received = Signal(str)
    finished = Signal()

    def __init__(self, client, messages):
        super().__init__()
        self.client = client
        self.messages = messages

    def run(self):
        for chunk in self.client.chat_stream(self.messages):
            if self.isInterruptionRequested():
                return
            self.chunk_received.emit(chunk)
        self.finished.emit()

class Session(QObject):
    message_received = Signal(str, str)

    def send_message(self, text):
        self._worker = ChatWorker(self._client, self.messages)

        # ALL connections MUST be QueuedConnection
        self._worker.chunk_received.connect(
            lambda c: self.message_received.emit(self.id, c),
            Qt.QueuedConnection
        )
        self._worker.finished.connect(
            self._on_complete,
            Qt.QueuedConnection
        )
        self._worker.error.connect(
            lambda e: self._on_error(e),
            Qt.QueuedConnection
        )
        self._worker.started.connect(
            lambda: self.status_changed.emit(self.id, "waiting"),
            Qt.QueuedConnection
        )
        self._worker.start()
```

---

## Enter-Send / Shift+Enter-Newline Pattern

Override `keyPressEvent` in a `QPlainTextEdit` subclass:

```python
class SendEdit(QPlainTextEdit):
    """Enter=send, Shift+Enter=newline."""

    send_pressed = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)  # newline
            else:
                self.send_pressed.emit()      # send
        else:
            super().keyPressEvent(event)
```

Connect in the parent:
```python
self.input_edit = SendEdit()
self.input_edit.send_pressed.connect(self._on_send)
self.input_edit.setPlaceholderText("Enter 发送, Shift+Enter 换行")
```

---

## Dark Theme as Default

Windows users expect dark UIs for developer tools. Apply via QSS at app startup:

```python
# In main_window.py
from theme import DARK_THEME

class MainWindow(QMainWindow):
    def __init__(self):
        self._dark_mode = True
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(DARK_THEME if self._dark_mode else LIGHT_THEME)

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()
```

Key QSS for dark theme:
```css
QMainWindow { background: #1e1e1e; }
QWidget { background: #1e1e1e; color: #d4d4d4; }
QTextBrowser { background: #1e1e1e; color: #d4d4d4; font-size: 15px; }
QPlainTextEdit { background: #252526; color: #d4d4d4; border: 1px solid #3c3c3c; }
QTabBar::tab:selected { background: #1e1e1e; border-bottom: 2px solid #4fc3f7; }
QPushButton { background: #0e639c; color: #fff; }
QMenuBar { background: #2d2d2d; color: #d4d4d4; }
QStatusBar { background: #007acc; color: #fff; }
```

Font sizes should be **14-15px minimum** on Windows — 10px is unreadable on modern high-DPI displays.

---

## Streaming UI Updates in QTextBrowser

For real-time streaming of LLM responses:

```python
class ChatDisplay(QTextBrowser):
    def append_message(self, role, content):
        """Render a complete message with HTML."""
        html = self._render_message(role, content)
        self.append(html)
        self._scroll_to_bottom()

    def append_chunk(self, content):
        """Append plain text to the last message (streaming)."""
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)     # go to end
        self.setTextCursor(cursor)
        self.insertPlainText(content)       # insert as plain text
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
```

---

## Signal Chain for Multi-Session Architecture

```
User Input
  -> MainWindow._on_files_dropped()          [main thread]
    -> tab.display.append_message("user", ...) [main thread, immediate]
    -> Session.send_message()                 [main thread]
      -> ChatWorker.start()                  [creates worker thread]
      -> ChatWorker.run()                    [worker thread]
        -> LLMClient.chat_stream()           [HTTP request in worker]
        -> chunk_received.emit(chunk)        [FROM worker thread]
          -> (QueuedConnection)              delivered to main thread
          -> Session.message_received.emit()
            -> SessionManager.message_received.emit()
              -> MainWindow._on_message_chunk()
                -> tab.display.append_chunk() [main thread, safe]
```

---

## Quick Reference: PySide6 Project Skeleton

```
project/
  main.py                # app = QApplication(sys.argv); w = MainWindow(); w.show()
  main_window.py         # QMainWindow + QTabWidget + menus/toolbar
  chat_tab.py            # ChatDisplay + SendEdit + InputPanel per tab
  session_manager.py     # SessionManager + Session + ChatWorker (QThread)
  file_handler.py        # File drag/drop + encoding detection
  clipboard_manager.py   # QClipboard wrapper
  settings_dialog.py     # QDialog for LLM config
  theme.py              # DARK_THEME / LIGHT_THEME QSS strings
  llm_client.py          # httpx-based streaming API client
```

---

## Pitfalls Checklist

- [ ] PIP_PREFIX, PIP_TARGET, PYTHONPATH env vars cleared before install/run
- [ ] All QThread signal connections use `Qt.QueuedConnection`
- [ ] Enter-Send overridden in keyPressEvent (not Ctrl+Enter)
- [ ] Dark theme as default with 14-15px fonts
- [ ] User message displayed BEFORE API call starts
- [ ] Chunks written to screen immediately (append_chunk at end of doc)
- [ ] Single signal emission (not double-emitting files + text separately)
- [ ] "Thinking" indicator shown while API is running
- [ ] No hardcoded ~/.hermes paths in GUI code
