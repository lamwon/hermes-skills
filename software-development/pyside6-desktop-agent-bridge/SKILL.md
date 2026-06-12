---
name: pyside6-desktop-agent-bridge
description: Transform a simple PySide6 LLM chat GUI into a full agent-powered desktop app by bridging to a subprocess running AIAgent via JSON lines over stdio.
---

# PySide6 Desktop Agent Bridge

Transform a simple PySide6 chat GUI (direct LLM API calls) into a full-featured agent desktop app by running the agent in a subprocess and communicating via JSON lines over stdin/stdout.

## Architecture

```
Desktop GUI (PySide6)
    ↓↑ JSON lines (stdin/stdout via subprocess.PIPE)
hermes_bridge.py  (subprocess, runs AIAgent from agent codebase)
    │
    ├── AIAgent.run_conversation()  ← full agent loop
    ├── tools, skills, memory, delegation
    └── streaming callbacks → JSON events
```

## Key Files

### 1. hermes_bridge.py — Agent-in-subprocess

Runs in the agent's Python venv. Imports AIAgent from the agent codebase. Communicates via JSON lines over stdout (all logging goes to stderr).

**stdin commands:**
```
{"type":"new_session"}                           → creates session
{"type":"send","session_id":"xxx","text":"...","files":[...]}
{"type":"cancel","session_id":"xxx"}
{"type":"exit"}
```

**stdout events:**
```
{"type":"ready","text":"..."}
{"type":"session_created","session_id":"xxx"}
{"type":"chunk","session_id":"xxx","text":"text token"}
{"type":"tool_start","session_id":"xxx","name":"web_search","args":"..."}
{"type":"tool_result","session_id":"xxx","name":"web_search","status":"ok"}
{"type":"status","session_id":"xxx","text":"thinking..."}
{"type":"done","session_id":"xxx"}
{"type":"error","session_id":"xxx","text":"error message"}
```

**Critical setup in create_agent():**

```python
def create_agent(self, model=None, provider=None, base_url=None, api_key=None):
    # Read config from ~/.hermes/config.yaml if no params given
    # Two formats supported:
    #   New: model.default + model.provider + model.base_url + model.api_key
    #   Old: default_provider + providers dict
    # Pass resolved params to AIAgent constructor:
    self.agent = AIAgent(
        quiet_mode=True,
        skip_context_files=True,
        session_id=sid,
        model=model,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        stream_delta_callback=on_stream_delta,
        tool_progress_callback=on_tool_progress,
        status_callback=on_status,
    )
```

**Callback signatures:**
```python
def on_stream_delta(text: str):      # text token (str) or None (flush)
def on_tool_progress(event_type: str, name: str, preview: str, args: dict, **kwargs):
    # event_type: "tool.started", "tool.completed", "reasoning.available"
def on_status(text: str):            # status update
```

### 2. acp_session.py — Bridge process manager (desktop side)

Manages the subprocess, reads stdout in a daemon thread, queues events per session.

**BridgeProcess** class:
- `start(event_callback)` — spawns subprocess, waits for "ready" signal
- `create_session()` — sends new_session, waits for session_created reply
- `send_message(sid, text, files)` — sends send command
- `cancel(sid)` — sends cancel
- `stop()` — sends exit, terminates process

**ACPSession** — replaces old LLM session:
- `get_pending(max_items)` — returns list of tuples for QTimer polling
- Events: `("chunk", text)`, `("tool_start", name, args)`, `("tool_result", name, status)`, `("done",)`, `("error", text)`

**Threading:**
```python
def reader_thread(out_queue):
    for line in iter(proc.stdout.readline, ""):
        out_queue.put(line)  # daemon thread
```

**QTimer polling in MainWindow:**
```python
def _poll_sessions(self):
    for sid, session in self.session_mgr.sessions.items():
        if sid in self._finished: continue
        events = session.get_pending(50)
        if not events: continue
        tab = self._get_tab(sid)
        if not tab: continue
        for event in events:
            event_type = event[0]
            if event_type == "chunk":
                text = event[1]
                if not self._buffer.get(sid):
                    tab.display.start_assistant()  # insert assistant header
                tab.display.append_assistant_chunk(text)
            elif event_type == "tool_start":
                tab.display.start_tool(event[1], event[2] if len(event)>2 else "")
            elif event_type == "tool_result":
                tab.display.end_tool(event[1], event[2] if len(event)>2 else "ok")
            elif event_type == "done":     mark_finished()
            elif event_type == "error":    tab.display.append_system_message(f"错误: {event[1]}")
```

## Pitfalls

1. **Windows select.select doesn't work on pipes** — use threading.Queue + reader thread instead
2. **Buffering kills latency** — set `bufsize=1` on Popen and `flush=True` on stdout writes from bridge
3. **Model config may be empty** — AIAgent with no model/provider fails silently. Always read from ~/.hermes/config.yaml before passing to AIAgent constructor
4. **run_agent.py may have *** corruption** — check for `credential_pool=***` and `os.get...EY` bugs with py_compile before use
5. **Desktop venv ≠ agent venv** — the bridge must run with the agent's Python (not the desktop's venv if different)
6. **Logging goes to stderr** — critical for bridge: all logging stderr, stdout reserved for JSON protocol only
7. **Session persistence** — ACPSession.get_pending() is called from QTimer (main thread), but events arrive from reader thread (background). Use a thread-safe deque with a lock.

## ChatDisplay: Thinking Process Visualization (No Background Color)

When users want to see the agent's **full thinking chain** (tool calls, analysis, intermediate results) without colored message bubbles:

```python
class ChatDisplay(QTextBrowser):
    """Clean display — no backgrounds, only borders and labels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        font = QFont("Microsoft YaHei", 15)
        self.setFont(font)
        self._has_assistant_header = False
        self._init_doc()

    def _init_doc(self):
        self.clear()
        self.document().setDefaultStyleSheet("""
            body { margin:0; padding:0; }
            code { background:#f0f2f5; padding:1px 4px; border-radius:3px; }
            pre { background:#f5f6f8; padding:12px; border-left:3px solid #bfc9d9; }
            a { color:#1a5276; }
        """)

    def append_user_message(self, content):
        # Blue top border + label, NO background
        html = f'''
        <div style="border-top:3px solid #1a5276; padding-top:10px; margin-top:18px;">
            <span style="color:#1a5276; font-size:13px; font-weight:bold; letter-spacing:1px;">
                &#x2501;&#x2501;&#x2501; 我 &#x2501;&#x2501;&#x2501;</span>
        </div>
        <div style="padding:10px 0 4px 0; font-size:16px; line-height:1.9; color:#222;">
            {markdown.markdown(content, extensions=self._md_ext)}
        </div>'''
        self.append(html)

    def start_assistant(self):
        self._has_assistant_header = False

    def append_assistant_chunk(self, text):
        if not self._has_assistant_header:
            self.append('''
            <div style="border-top:2px solid #dcdfe6; padding-top:10px; margin-top:10px;">
                <span style="color:#666; font-size:13px; font-weight:bold; letter-spacing:1px;">
                    &#x2501;&#x2501;&#x2501; 桌面助手 &#x2501;&#x2501;&#x2501;</span>
            </div>
            <div style="padding:8px 0 4px 0; font-size:16px; line-height:1.9; color:#222;">''')
            self._has_assistant_header = True
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self._scroll_bottom()

    def start_tool(self, name, args=""):
        """Orange left border + tool name."""
        short = args[:120] if args else ""
        html = f'''
        <div style="border-left:3px solid #e67e22; padding:6px 12px; margin:6px 0 2px 0;">
            <span style="color:#e67e22; font-size:13px; font-weight:bold;">&#x25B6; {name}</span>
            <span style="color:#888; font-size:13px; padding-left:8px;">{short}</span>
        </div>'''
        self.append(html)

    def end_tool(self, name, status="ok"):
        """Green/red left border + checkmark."""
        color = "#27ae60" if status == "ok" else "#e74c3c"
        html = f'''
        <div style="border-left:3px solid {color}; padding:2px 12px 6px 12px; margin:0 0 6px 0;">
            <span style="color:{color}; font-size:12px;">{"&#x2713;" if status=="ok" else "&#x2717;"} {name}</span>
        </div>'''
        self.append(html)

    def append_system_message(self, content):
        html = f'<div style="border-left:3px solid #3498db; padding:6px 12px; margin:6px 0;">{content}</div>'
        self.append(html)
```

**What this looks like in the chat:**
```
━━━━━ 我 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[user text — no bg, only blue top border]

  ▶ web_search  query text
  ✓ web_search (ok)

━━━━━ 桌面助手 ━━━━━━━━━━━━━━━━━━━━━━━━━━
[assistant response — streaming, no bg]
```

## Government Official Theme (政府公务风)

When transforming a cyberpunk/neon PySide6 theme to formal government style:

```python
# Color palette:
PRIMARY    = "#1a5276"  # deep official blue
SECONDARY  = "#2980b9"  # medium blue  
BG_PAGE    = "#f0f2f5"  # light gray background
BG_CARD    = "#ffffff"  # white card backgrounds
TEXT       = "#222222"  # dark text
TEXT_MUTED = "#555555"  # secondary text
BORDER     = "#dcdfe6"  # light border
BORDER_ACCENT = "#bfc9d9"  # medium border
```

Key CSS patterns (Qt stylesheet):
- QMainWindow, QWidget: `background: #f0f2f5; color: #222222; font-size: 14px;`
- Tab selected: `background: #ffffff; color: #1a5276; border-top: 2px solid #1a5276;`
- QPushButton:hover: `background: #e8f0fe; border-color: #1a5276; color: #1a5276;`
- QMenuBar: `background: #ffffff; border-bottom: 1px solid #dcdfe6;`
- QTextBrowser: `background: #f7f8fa; color: #222222; padding: 20px; font-size: 15px;`
- Status bar: no emoji, plain Chinese text

Message bubbles (HTML inside QTextBrowser):
- User bubble: `background:#e8f0fe; border-left:4px solid #1a5276;`
- Assistant bubble: `background:#ffffff; border-left:4px solid #bfc9d9;`
- System bubble: `background:#fff8e6; border-left:4px solid #e6a817;`
- All left-aligned (`text-align:left`), 16px font, 1.8 line-height

## Verification

```bash
# Syntax check all files
cd /path/to/desktop && ./venv/Scripts/python.exe -m py_compile *.py

# Test bridge startup
printf '{"type":"new_session"}\n{"type":"exit"}\n' | \
  /path/to/agent-venv/bin/python hermes_bridge.py 2>/dev/null

# Integration test (create session, send message, stream response)
python -c "
from acp_session import ACPSessionManager
mgr = ACPSessionManager()
sid = mgr.create_session('test')
mgr.send_message(sid, 'hi')
# Poll get_pending() in a loop until done/finished
"
```
