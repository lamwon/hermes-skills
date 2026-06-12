---
name: acp-vscode-debug
title: ACP VS Code Integration Debugging
description: Systematic approach to debugging ACP (Agent Communication Protocol) integration with VS Code when the agent shows "connected but disconnected" (green light but handshake failure) or "exited code=0, server not responding".
category: devops
---

# ACP VS Code Integration Debugging

When VS Code's ACP Client extension shows a green light (process starts) but "disconnected" status, the ACP JSON-RPC handshake is failing at the stdio transport level. This guide covers the systematic debugging approach.

## Environment Detection

First, determine **which VS Code extension** handles the ACP connection:

1. **`anysphere.acp-client`** (the official ACP Client extension) — reads `acpClient.agents` from VS Code settings, connects via `acp_registry/agent.json`
2. **Extension-bundled ACP client** (e.g., `hermes-agent.hermes-vscode`) — has its **own built-in** `ACPClient` class with hardcoded paths. Does NOT read `acpClient.agents` settings!

**How to tell:** Look in `%USERPROFILE%\.vscode\extensions\` for installed extensions. If you find `hermes-agent.hermes-vscode-x.y.z`, check its `out/acpClient.js` for a `findHermesCommand()` method with hardcoded paths.

## Key Extension-Bundled Client Behaviors

When debugging a bundled client (like `hermes-vscode`):

1. **`findHermesCommand()` returns the launch config**. The extension has its own hardcoded search order. Common paths: `D:\Hermes\hermes.bat`, PATH lookup, `.venv` fallback.
2. **`session_id` (snake_case)** — The extension may send `session_id` in `session/prompt` params, not `sessionId` (camelCase). Both must be supported.
3. **`protocolVersion: 6`** — Some bundled extensions send protocol version 6, not the standard 1.
4. **Extension `start()` method** spawns process, waits 1500ms, then `tryInit()` retries `initialize()` up to 20 times (1s intervals). If all fail: "ACP server did not respond after 20 attempts".
5. **`process.on('exit')`** fires `setStatus('disconnected')` — this is the "green light to disconnected" cycle that users see.

### Critical: Two spawn anti-patterns in `cmd /c` (THE #1 ROOT CAUSE)

Many bundled extensions have fallback paths that use complex `cmd /c` command strings:

**ANTI-PATTERN #1: `&&` chaining with nested quotes**
```javascript
args: ['/c', `cd /d "${dir}" && "${python}" -u -c "..."`]
// Process starts and immediately exits (code=1).
// cmd.exe chokes on the nested double-quotes inside the `&&` string.
```

**ANTI-PATTERN #2: Array args after `cmd /c` (MOST DANGEROUS)**
```javascript
args: ['/c', pythonExe, '-u', '-c', 'import ...']
// Process exits immediately (code=0, signal=null).
// cmd /c only uses the FIRST element as the command string.
// Python starts WITHOUT -c flag (interactive mode), stdin closes.
// This creates the "green light -> disconnected in 2 seconds" pattern.
```

**THE ROOT CAUSE**: `cp.spawn('cmd', ['/c', a, b, c], {windowsVerbatimArguments: true})` does NOT combine array elements into a single command line the way cmd.exe in a terminal would. Only element `a` is passed as the command to `cmd /c`; `b` and `c` are visible only to cmd.exe's argument parser which ignores them. Result: the program in `a` (e.g., python.exe) starts without its intended flags and exits immediately.

**THE PROVEN FIX**: Create a standalone `.bat` launcher. Always use `['/c', 'launcher.bat']` — no array args after `/c`, no `&&` chaining, no nested quotes.

Create `acp-launcher.bat`:
```batch
@echo off
setlocal
set "ROOT=%~dp0portable-hermes-agent"
set "PYTHON=%ROOT%\python_embedded\python.exe"
set "PYTHONIOENCODING=utf-8"
chcp 65001 >nul 2>&1
cd /d "%ROOT%"
"%PYTHON%" -u -B -c "import sys; sys.path.insert(0, '%ROOT:/=\\%'); from acp_adapter.entry import main; main()"
endlocal
```

Then in `findHermesCommand()`:
```javascript
findHermesCommand() {
    const launcher = 'D:\\Hermes\\acp-launcher.bat';
    if (fs.existsSync(launcher)) {
        return { command: 'cmd', args: ['/c', launcher] };
    }
    return null;
}
```

## Root Causes (most common first)

### 1. VS Code settings.json missing ACP Client configuration
**The "exited code=0, server not responding" error often means VS Code doesn't know where to find the agent.**

**Symptom:** VS Code ACP extension shows red disconnected state with "ACP server did not respond" and "exited code=0, signal=null". Agent starts and exits immediately because VS Code never sent it an initialize request.

**Cause:** The ACP Client VS Code extension requires explicit configuration in `settings.json` pointing to the registry directory.

**Fix:** Add to VS Code `settings.json` (`%APPDATA%\Code\User\settings.json` on Windows):
```json
{
  "acpClient.agents": [
    {
      "name": "hermes-agent",
      "registryDir": "D:\\path\\to\\hermes-agent\\acp_registry"
    }
  ],
  "acpClient": {
    "agents": [
      {
        "name": "hermes-agent",
        "registryDir": "D:\\path\\to\\hermes-agent\\acp_registry"
      }
    ]
  }
}
```
Use both formats to be safe.

### 2. Batch/Shell script polluting stdout
If the agent is launched via a `.bat` or `.sh` script that echoes anything to stdout before the Python process starts, it corrupts the JSON-RPC over stdio protocol.

**Symptom:** VS Code shows green dot but "disconnected" within seconds. Direct subprocess test of the agent (via Python) works fine.

**Fix:** Redirect all informational output to stderr:
```batch
echo Loading Hermes Agent... >&2
```

### 3. File corruption in ACP adapter code
The `acp_adapter/auth.py` and `acp_adapter/server.py` files can develop corrupted lines with `***` placeholders.

**Diagnosis:**
```bash
python -c "import py_compile; py_compile.compile('acp_adapter/auth.py', doraise=True)"
python -c "import py_compile; py_compile.compile('acp_adapter/server.py', doraise=True)"
```

**Common corruptions:**
- `acp_adapter/auth.py` line 13: `api_key=runtim...ey")` -> `api_key = runtime.get("api_key")`
- `acp_adapter/server.py` `initialize()`: `auth_methods=***` -> proper `AuthMethod(...)` construction

### 4. Registry command resolution
On Windows, `"command": "hermes"` in `acp_registry/agent.json` may resolve to `hermes.bat` instead of `hermes.exe`.

**Fix:**
```json
"command": "hermes.exe"
```

### 5. TypeErrors in extension JS code
Check VS Code Developer Tools Console (`Ctrl+Shift+P` -> `Developer: Toggle Developer Tools` -> Console) for errors like `TypeError: e is not iterable`.

Common cause: `for (const x of Object.keys(something))` where `something` is `undefined`. When `findHermesCommand()` returns no `envSetup` key and `start()` unconditionally iterates it.

**Fix:** Ensure the extension's `start()` guards iteration with `if (cmdInfo.envSetup)`, or don't include `envSetup` in the returned object at all.

## Debugging Toolkit

### Direct ACP server test
```python
import subprocess, json, threading, time

proc = subprocess.Popen(
    ['cmd', '/c', 'D:\\path\\acp-launcher.bat'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)

all_out = []; running = True
def co():
    while running:
        l = proc.stdout.readline()
        if l: all_out.append(l.decode().strip())
threading.Thread(target=co, daemon=True).start()

time.sleep(3)
poll = proc.poll()
print(f'Alive: {poll is None}')  # Must be True

# Send INIT (version 6 matches VS Code extension)
proc.stdin.write(json.dumps({
    'jsonrpc':'2.0','id':1,'method':'initialize',
    'params':{'protocolVersion':6,'capabilities':{},'clientInfo':{'name':'test','version':'1.0'}}
}).encode() + b'\n')
proc.stdin.flush()
time.sleep(3)

# SESSION/NEW
proc.stdin.write(json.dumps({
    'jsonrpc':'2.0','id':2,'method':'session/new',
    'params':{'cwd':'D:\\path','mcpServers':[]}
}).encode() + b'\n')
proc.stdin.flush()
time.sleep(3)

# PROMPT
proc.stdin.write(json.dumps({
    'jsonrpc':'2.0','id':3,'method':'session/prompt',
    'params':{'session_id':'test-session','prompt':[{'type':'text','text':'hi'}]}
}).encode() + b'\n')
proc.stdin.flush()
time.sleep(3)

running = False
time.sleep(1)
print(f'Responses: {len(all_out)}')
for l in all_out:
    print(f'  {l[:250]}')
proc.kill()
```

Expect 3 responses (INIT result, sessionId, prompt result). If you don't get all 3, the server or communication layer is broken.

## Key Protocol Details

- **ACP protocol version**: 1 (defined in `acp/meta.py`), but some clients send version 6
- **Transport**: JSON-RPC 2.0 over stdio via `sys.stdout.buffer.write()`
- **Windows stdio**: `acp/stdio.py` -> `_windows_stdio_streams()` creates `_StdoutTransport`
- **session/new requires `mcpServers`**: In ACP 0.8.1+, `mcpServers` is **required** (not Optional)
- **Auth methods**: Must construct `AuthMethod` objects with `id`, `name`, and `description` fields
- **Notifications vs Responses**: Status updates are `session/update` notifications (no `id`). Final response has matching `id` of the `session/prompt` request.

## Verification Flow

## Key Finding: Config Already Correct — Just Open VS Code

**This is the most common scenario**: the user's `~/.hermes/config.yaml` and `~/.hermes/.env` are already properly configured with the desired model and API key. The ACP adapter reads these at startup (confirmed by log: `Loaded env from C:\\Users\\Windows\\.hermes\\.env`).

**No further configuration is needed** — the VS Code extension auto-launches the ACP adapter when you open the chat panel. The user just needs to:
1. Open VS Code
2. Press `Ctrl+Shift+I` or click the Hermes icon in the sidebar
3. Start chatting

## ACP Adapter Log Verification

When the ACP adapter starts successfully, the log shows:

```
Loaded env from C:\Users\Windows\.hermes\.env    <- config loaded OK
Starting hermes-agent ACP adapter                  <- process started
ACP client connected                               <- VS Code extension connected
```

If you see these 3 lines, the entire pipeline is working. No need to restart anything.

## Version-Specific Behavior: hermes-vscode 0.1.0

The bundled extension at version 0.1.0 (`hermes-agent.hermes-vscode-0.1.0`) has a **hardcoded `findHermesCommand()`** in `out/acpClient.js` that **completely bypasses** `acp_registry/agent.json`'s `command` field.

**It spawns Python directly:**
```javascript
pythonExe: 'D:\\Hermes\\portable-hermes-agent\\python_embedded\\python.exe',
args: ['-u', '-m', 'acp_adapter.entry'],
```

**Hardcoded env setup:**
```javascript
envSetup: {
    PYTHONPATH: 'D:\\Hermes\\portable-hermes-agent;D:\\Hermes\\portable-hermes-agent\\python_embedded\\Lib\\site-packages',
    PYTHONIOENCODING: 'utf-8',
    HERMES_ROOT: 'D:\\Hermes\\portable-hermes-agent',
    HERMES_HOME: 'C:\\Users\\Windows\\.hermes',
}
```

**Implications:**
- The `agent.json`'s `"command": "hermes.exe"` field is **not used** by the bundled extension
- The `acpClient.agents` settings in VS Code `settings.json` are also **not used** by the bundled extension
- Changing agent.json won't affect how the extension launches the adapter
- To change the launch config, you must modify `acpClient.js` directly

## Git Bash Background vs. VS Code Spawn

- **When launched from Git Bash** (`hermes acp &`): the process exits when the shell session ends
- **When spawned by VS Code extension** (`cp.spawn()`): the process persists as long as the extension needs it
- **Do NOT manually start ACP in Git Bash** — let the VS Code extension handle it. The extension's `start()` method spawns the process, waits 1500ms, then retries `initialize()` up to 20 times

## Verification Flow
10. **FULLY RESTART VS CODE** — "Developer: Reload Window" is NOT enough; close and reopen
11. **Check ACP adapter logs** — look for the 3 success lines (env loaded, adapter started, client connected). If these appear, the config and connection are working fine.
12. **Final sanity check**: If `~/.hermes/config.yaml` has the correct model/provider and `.env` has the API key, AND the ACP adapter logs show "Loaded env" + "ACP client connected" — everything is working. Just use `Ctrl+Shift+I` in VS Code to start chatting.

## Quick Patch Template (Bundled Client)

For `hermes-vscode` or similar bundled clients, create `acp-launcher.bat` and replace `findHermesCommand()`:

```javascript
findHermesCommand() {
    const launcher = 'D:\\Hermes\\acp-launcher.bat';
    if (fs.existsSync(launcher)) {
        return { command: 'cmd', args: ['/c', launcher] };
    }
    // Fallback
    const hermesBat = 'D:\\Hermes\\hermes.bat';
    if (fs.existsSync(hermesBat)) {
        return { command: 'cmd', args: ['/c', hermesBat, 'acp'] };
    }
    return null;
}
```

**Golden rule**: Always return `['/c', pathToBat]` — exactly TWO args after `/c`. No array of separate program arguments. No `&&` chaining in a single string. Let the `.bat` file handle all the complexity internally.
