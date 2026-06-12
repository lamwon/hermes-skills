---
name: cc-switch-model-routing
description: Troubleshooting Claude Code model routing through cc-switch proxy — diagnosing why model changes in settings.json don't take effect and how the proxy rewrites model names.
---

# CC-Switch Model Routing Debug

## Problem

You change the model in Claude Code's `settings.json` (e.g., to `deepseek-v4-pro`), but:
- DeepSeek balance page only shows Flash usage
- No Pro usage ever appears
- The model doesn't seem to be taking effect

## Root Cause

**cc-switch** is a local proxy application that sits between Claude Code and the upstream API. It intercepts ALL requests and **forcibly rewrites the model name** before forwarding. No matter what model you set in `settings.json`, cc-switch overrides it.

Request chain:
```
Claude Code (settings.json says deepseek-v4-pro)
  -> cc-switch proxy (127.0.0.1:port) -- rewrites model name here!
    -> Upstream API (e.g., api.deepseek.com/anthropic/v1/messages)
```

## Diagnosis Steps

### 1. Check if cc-switch is running
```bash
# Find the process
tasklist //FI "IMAGENAME eq cc-switch.exe" //FO LIST
# Or check the listening port
netstat -ano | grep <port>     # e.g., port 15721
```

### 2. Check cc-switch logs
Logs are at `~/.cc-switch/logs/cc-switch.log`. Look for lines showing:
```
[Claude] >>> 请求 URL: https://api.deepseek.com/... (model=<actual-model-sent>)
```

If all requests show a different model than what settings.json says, cc-switch is rewriting it.

### 3. Check Claude Code settings.json
Located at `~/.claude/settings.json`.
```json
{
  "model": "deepseek-v4-pro",
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:<port>",
    "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED"
  }
}
```

If `ANTHROPIC_BASE_URL` points to localhost, traffic goes through cc-switch.

## Fix — Method A: GUI (recommended if cc-switch is visible)

The cc-switch is a desktop GUI application (`CC Switch`, exe at `%LOCALAPPDATA%\\Programs\\CC Switch\\cc-switch.exe`). To fix model routing via GUI:

1. **Open CC Switch GUI** — find it in system tray or start menu
2. **Navigate to Claude provider settings**
3. **Change the target model** from `deepseek-v4-flash` to `deepseek-v4-pro` (or whatever model you want)
4. **Save and restart** Claude Code

## Fix — Method B: Direct SQLite database modification

If the GUI is not accessible or you need to automate the fix, modify cc-switch's SQLite database directly.

Database path: `~/.cc-switch/cc-switch.db`

### Key database schema

The `providers` table stores provider configurations in a `settings_config` JSON column. The relevant env vars controlled by cc-switch:

| Env Var | Purpose |
|---------|---------|
| `ANTHROPIC_MODEL` | Default model sent for all requests |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Fast/cheap model mapping |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Balanced model mapping |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Best model mapping |

Also, `proxy_live_backup` table may contain a backup of the original Claude Code settings. And the `proxy_request_logs` table records what model was actually used per request.

### Step-by-step SQLite fix

```python
import sqlite3, json, os, subprocess

db_path = os.path.expanduser("~/.cc-switch/cc-switch.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Update the Claude provider's env vars in settings_config
c.execute("SELECT id, settings_config FROM providers WHERE app_type='claude'")
for pid, config_str in c.fetchall():
    config = json.loads(config_str)
    # Change ALL model references from flash to pro
    for key in list(config.get('env', {})):
        if 'MODEL' in key and config['env'][key] == 'deepseek-v4-flash':
            config['env'][key] = 'deepseek-v4-pro'
    c.execute("UPDATE providers SET settings_config = ? WHERE id = ?",
              (json.dumps(config, ensure_ascii=False), pid))

# 2. Update the live backup (if it exists)
c.execute("SELECT rowid, original_config FROM proxy_live_backup WHERE app_type='claude'")
for rid, config_str in c.fetchall():
    backup = json.loads(config_str)
    if backup.get('model') == 'deepseek-v4-flash':
        backup['model'] = 'deepseek-v4-pro'
    for key in list(backup.get('env', {})):
        if 'MODEL' in key and backup['env'][key] == 'deepseek-v4-flash':
            backup['env'][key] = 'deepseek-v4-pro'
    c.execute("UPDATE proxy_live_backup SET original_config = ? WHERE rowid = ?",
              (json.dumps(backup, ensure_ascii=False), rid))

# 3. Also sync settings.json
settings_path = os.path.expanduser("~/.claude/settings.json")
with open(settings_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)
settings['model'] = 'deepseek-v4-pro'
with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2)

conn.commit()
conn.close()
print("Database updated. Now restart cc-switch and Claude Code.")
```

### Restart cc-switch

```bash
# Find and kill the cc-switch process
tasklist //FI "IMAGENAME eq cc-switch.exe" //FO CSV
# Get PID and kill it
taskkill //F //PID <PID>

# Or start it again
start "" "%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe"
```

### Verify the fix

Three verification methods, ordered from most reliable to least:

#### Option A: Query proxy_request_logs table (most reliable)
The `proxy_request_logs` table records every proxied request with the actual model sent upstream:
```python
import sqlite3, os
db_path = os.path.expanduser("~/.cc-switch/cc-switch.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("""
    SELECT model, request_model, status_code, created_at
    FROM proxy_request_logs
    WHERE app_type='claude'
    ORDER BY created_at DESC LIMIT 5
""")
for row in c.fetchall():
    print(f"model={row[0]}, original_request={row[1]}, status={row[2]}")
conn.close()
```
The `model` field shows what was actually sent upstream; `request_model` shows what Claude Code originally requested. If these differ, cc-switch is still rewriting.

#### Option B: Check cc-switch logs
```bash
grep "model=" ~/.cc-switch/logs/cc-switch.log | tail -3
```
Look for `model=<expected-model>` in the forwarded URL line.

#### Option C: Make a test request and check DeepSeek balance page
Run Claude Code briefly, then check the DeepSeek platform balance page.

## Settings.json Manually Modified (Not Proxy Takeover)

When `~/.claude/settings.json` has been manually changed to bypass cc-switch entirely:

### Symptoms
- `ANTHROPIC_BASE_URL` points to a different port (e.g., `15722` instead of cc-switch's `15721`)
- `ANTHROPIC_AUTH_TOKEN` is a real API key (starts with `sk-...`) instead of `PROXY_MANAGED`
- `ANTHROPIC_MODEL` is a different model (e.g., `qwen3.7-max` instead of `deepseek-v4-flash`)
- cc-switch process is still running and its database still has correct DeepSeek config
- `proxy_request_logs` show older successful requests with `deepseek-v4-flash` and newer failed ones with the wrong model

### Fix: Rewrite settings.json back to cc-switch proxy

```python
import json, os

settings_path = os.path.expanduser("~/.claude/settings.json")
current = json.load(open(settings_path, 'r'))

new_settings = {
    "model": "deepseek-v4-flash",  # or whatever your target model is
    "env": {
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:15721",  # cc-switch default port
        "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED",  # let cc-switch handle auth
        "ANTHROPIC_MODEL": "deepseek-v4-flash",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash"
    },
    "permissions": current.get("permissions", {})
}

with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(new_settings, f, indent=2, ensure_ascii=False)
```

### Verify
1. Restart Claude Code (close and reopen the VS Code panel)
2. Check `proxy_request_logs` in cc-switch DB shows `deepseek-v4-flash` again
3. Check DeepSeek balance page to confirm Flash usage

### Prevention
If you need to temporarily use a different model, use the cc-switch GUI to change the model — never edit `settings.json` directly. The cc-switch GUI updates the database AND syncs env vars correctly.

## "ConnectionRefused" / Proxy Not Responding Diagnosis

When Claude Code shows `API Error: Unable to connect to API (ConnectionRefused)`, the proxy is either down or not forwarding. **Don't jump to restarting immediately** — check which layer is failing:

### Step 1: Is cc-switch running?
```bash
wmic process where "name like '%%cc-switch%%'" get name,processid
```
Or via tasklist (Git Bash):
```bash
tasklist | grep -i cc-switch
```

### Step 2: Is the proxy port responding?
```bash
curl -v http://127.0.0.1:<port> --max-time 5 2>&1 | head -5
```
- If you get ANY HTTP response (even 404/405), the proxy socket is alive
- If you get `Connection refused`, the proxy process is dead or listening on a different port

### Step 3: Is DeepSeek API accessible?
```bash
curl -s -o /dev/null -w "HTTP %{http_code} Time: %{time_total}s\n" \
  https://api.deepseek.com/v1/models --max-time 10
```
- HTTP 401 = API is reachable (Good — the issue is auth or proxy config)
- Connection timeout = DeepSeek is blocked in China

### Step 4: Check for abnormal exit recovery in logs
```bash
grep -i "异常退出|接管残留|restore|recover" ~/.cc-switch/logs/cc-switch.log | tail -5
```
Look for `检测到上次异常退出` — cc-switch may have auto-recovered from a crash. When this happens, sometimes Claude Code's session cache still points to a stale connection.

### Step 5: Try a real proxy-forwarded request
```bash
curl -s http://127.0.0.1:<port>/anthropic/v1/messages -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: test" \
  -d '{"model":"deepseek-v4-flash","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}' \
  --max-time 15 2>&1
```
- Empty output, or curl hanging = proxy can't reach DeepSeek (check network/GFW)
- HTTP 401/404 = proxy IS forwarding but auth is wrong

### Quick fix for abnormal exit state
1. Open cc-switch GUI → Claude provider → **取消接管** (un-takeover) → **重新接管** (re-takeover)
2. This resets the proxy state without restarting
3. If that fails, restart cc-switch:
```bash
taskkill //F //PID <PID>
start "" "%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe"
```
4. Restart Claude Code (in VS Code: close and reopen Claude Code panel)

### Architecture reminder: the proxy has two distinct failure modes
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `ConnectionRefused` immediately | Proxy not listening / wrong port | Restart proxy, check port |
| Hangs then times out | Proxy running but can't reach upstream | Check network (GFW, VPN) |
| `401 Unauthorized` | API key issue | Re-enter key in cc-switch GUI |
| Model not changing after settings.json edit | Proxy rewriting model (not a ConnectionRefused issue) | Change model in cc-switch GUI/database |

## Important caveat: settings.json may already say the right model

A common trap: `~/.claude/settings.json` already shows `"model": "deepseek-v4-pro"`, leading you to think the fix is somewhere else. **This is misleading** — cc-switch overrides the model at the proxy level regardless of what settings.json says. Always query `proxy_request_logs` or check cc-switch logs to see what actually gets sent upstream.

### The `PROXY_MANAGED` sentinel

When cc-switch takes over, it sets `ANTHROPIC_AUTH_TOKEN` to `"PROXY_MANAGED"` in `settings.json`. This is a **sentinel value** meaning "cc-switch handles authentication using its own internally stored API key" — NOT a real token. The proxy strips this sentinel and injects the real key from its database before forwarding the request. This is another indicator that your traffic is going through cc-switch: if you see `PROXY_MANAGED`, the proxy controls both routing AND auth.

### Multiple env vars override model — not just ANTHROPIC_MODEL

cc-switch sets **four separate** model env vars in its internal config, all of which must be updated together:

| Env Var | When it's used |
|---------|---------------|
| `ANTHROPIC_MODEL` | Default model for all requests |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | When Claude Code uses a "fast" sub-command |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | When Claude Code uses the "balanced" sub-command |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | When Claude Code uses the "best" sub-command |
| `ANTHROPIC_REASONING_MODEL` | Extended thinking/reasoning requests |

Claude Code may choose different sub-models depending on task complexity. If only `ANTHROPIC_MODEL` is changed but the `_DEFAULT_*` vars still point to the old model, some requests will still use the wrong model. Always update all model env vars to the same target model.

## Full cc-switch database schema reference

Key tables in `~/.cc-switch/cc-switch.db`:

| Table | Purpose |
|-------|---------|
| `providers` | Provider configs with JSON `settings_config` column (model env vars live here) |
| `provider_endpoints` | API endpoint URLs per provider |
| `proxy_config` | Proxy listen address/port, failover settings per app type |
| `proxy_request_logs` | Every proxied request with model, tokens, latency, cost |
| `proxy_live_backup` | Backup of original client configs before cc-switch took over |
| `settings` | Key-value store for app-wide settings |
| `model_pricing` | Model pricing data (cost per million tokens) |
| `provider_health` | Health check status per provider |
| `usage_daily_rollups` | Daily aggregated usage stats |

### proxy_request_logs columns (for troubleshooting)

```
request_id, provider_id, app_type, model, request_model,
input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens,
input_cost_usd, output_cost_usd, cache_read_cost_usd, cache_creation_cost_usd,
total_cost_usd, latency_ms, first_token_ms, duration_ms,
status_code, error_message, session_id, provider_type,
is_streaming, cost_multiplier, created_at, data_source
```

The `model` vs `request_model` comparison reveals whether cc-switch is still rewriting.

## Configuration files

| Component | Path |
|-----------|------|
| Claude Code settings | `~/.claude/settings.json` |
| Claude Code local settings | `~/.claude/settings.local.json` |
| cc-switch logs | `~/.cc-switch/logs/cc-switch.log` |
| cc-switch database | `~/.cc-switch/cc-switch.db` |
| cc-switch binary | `%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe` |
| cc-switch app data | `%APPDATA%\com.ccswitch.desktop\` |

## Adding a New Provider to CC-Switch

CC Switch stores provider configurations in a SQLite database, not in JSON config files. To add a new provider:

### 1. Locate the database

```
~/.cc-switch/cc-switch.db
```

### 2. Understand the providers table schema

```sql
providers(id TEXT, app_type TEXT, name TEXT, settings_config TEXT, website_url TEXT,
         category TEXT, created_at INTEGER, sort_index INTEGER, notes TEXT,
         icon TEXT, icon_color TEXT, meta TEXT, is_current BOOLEAN,
         in_failover_queue BOOLEAN, cost_multiplier TEXT, limit_daily_usd TEXT,
         limit_monthly_usd TEXT, provider_type TEXT)
```

Key columns:
- `app_type`: `"claude"`, `"codex"`, `"gemini"`, `"opencode"`, `"hermes"` — determines which app type this provider is available for
- `settings_config`: JSON with `env` object containing API-specific env vars
- `meta`: JSON with `apiFormat` (e.g. `"anthropic"` or `"openai"`), `commonConfigEnabled`, `usage_script`

### 3. JSON formats by API format type

**For Anthropic-format providers** (e.g., DeepSeek's `/anthropic` endpoint):
```python
settings_config = {
    "env": {
        "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
        "ANTHROPIC_AUTH_TOKEN": "sk-...",
        "ANTHROPIC_MODEL": "deepseek-v4-flash",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash"
    },
    "includeCoAuthoredBy": False
}

meta = {
    "commonConfigEnabled": True,
    "usage_script": {"enabled": True, "language": "javascript", "code": "",
                     "timeout": 10, "templateType": "balance", "autoQueryInterval": 5},
    "endpointAutoSelect": True,
    "apiFormat": "anthropic"
}
```

**For OpenAI-format providers** (e.g., Qwen/DashScope):
```python
settings_config = {
    "env": {
        "OPENAI_BASE_URL": "https://ws-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
        "OPENAI_API_KEY": "sk-..."
    },
    "includeCoAuthoredBy": False
}

meta = {
    "commonConfigEnabled": True,
    "usage_script": {"enabled": True, "language": "javascript", "code": "",
                     "timeout": 10, "templateType": "balance", "autoQueryInterval": 5},
    "endpointAutoSelect": True,
    "apiFormat": "openai"
}
```

### 4. Insert the provider and endpoint

```python
import sqlite3, json, uuid, time

db_path = os.path.expanduser("~/.cc-switch/cc-switch.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

new_id = str(uuid.uuid4())
now_ms = int(time.time() * 1000)

cursor.execute("""
    INSERT INTO providers (id, app_type, name, settings_config, website_url, category,
                          created_at, sort_index, notes, icon, icon_color, meta,
                          is_current, in_failover_queue, cost_multiplier,
                          limit_daily_usd, limit_monthly_usd, provider_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    new_id, "claude", "Qwen API",
    json.dumps(settings_config),      # settings_config JSON
    "https://bailian.console.aliyun.com",  # website_url
    "cn_official",                    # category: "official", "cn_official", "custom"
    now_ms, None, None,               # created_at, sort_index, notes
    None, "#FF6A00",                  # icon, icon_color
    json.dumps(meta),                 # meta JSON
    0, 0, "1.0", None, None, None     # is_current, in_failover_queue, cost_multiplier...
))

# Also add a provider_endpoint
cursor.execute("SELECT MAX(id) FROM provider_endpoints")
max_id = cursor.fetchone()[0] or 0
cursor.execute("""
    INSERT INTO provider_endpoints (id, provider_id, app_type, url, added_at)
    VALUES (?, ?, ?, ?, ?)
""", (max_id + 1, new_id, "claude",
      "https://ws-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1", now_ms))

conn.commit()
conn.close()
```

### 5. Restart CC Switch

The changes take effect only after restarting:
```bash
taskkill //F //PID <pid>
start "" "%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe"
```

### Quick data discovery

If you need to find where CC Switch stores data:
- Main database: `~/.cc-switch/cc-switch.db` (SQLite)
- Settings: `~/.cc-switch/settings.json`
- Logs: `~/.cc-switch/logs/cc-switch.log`
- Backups: `~/.cc-switch/backups/`
- App binary: `%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe` or `D:\CC-Switch\cc-switch.exe`
- Portable INI: `D:\CC-Switch\portable.ini` (contains `portable=true`)
- Electron/WebView data: `%LOCALAPPDATA%\com.ccswitch.desktop\EBWebView\Default\` (mostly browser internal data, not app config)

### Pitfalls when adding providers

- **CC Switch must be closed** when modifying the database directly (SQLite lock issues)
- **Must add BOTH** a `providers` row AND a `provider_endpoints` row — the endpoint table is queried separately
- The `is_current=1` flag means "currently selected" — only set this if you want the new provider to be active immediately
- `app_type` determines which proxy this provider appears under (claude proxy vs codex proxy vs gemini proxy)
- For OpenAI-format claude providers, use `apiFormat: "openai"` in meta — cc-switch translates Anthropic API calls to OpenAI format on the fly

## Pitfalls

- Changing only `settings.json` is insufficient — cc-switch overrides the model at the proxy level
- cc-switch runs automatically at startup and persists its state across reboots
- cc-switch may also manage model pricing/usage tracking internally
- Restart both cc-switch AND Claude Code after making changes
