---
name: cc-switch-provider-database-edit
description: Add or modify CC Switch providers by directly editing its SQLite database, including configuring API endpoints, models, and troubleshooting SSL issues.
---

# CC Switch Provider Database Edit

Add/modify CC Switch providers by directly editing its SQLite database, bypassing the UI.

## Database Location

```
C:\Users\<user>\.cc-switch\cc-switch.db
```

## Key Tables

### `providers` table

Core provider configuration. Key columns:

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | UUID for the provider |
| app_type | TEXT | `claude`, `codex`, `gemini`, `opencode`, `hermes` |
| name | TEXT | Display name in CC Switch UI |
| settings_config | TEXT | JSON with `env` dict (API keys, URLs, models) |
| website_url | TEXT | Provider website |
| category | TEXT | `official`, `cn_official`, `custom` |
| created_at | INTEGER | Unix timestamp in ms |
| is_current | INTEGER | 0 or 1 |
| icon_color | TEXT | Hex color like `#FF6A00` |
| meta | TEXT | JSON with `apiFormat`, `commonConfigEnabled`, `endpointAutoSelect`, `usage_script` |
| cost_multiplier | TEXT | e.g. `"1.0"` |
| icon | TEXT | Provider icon name (e.g. `deepseek`, `openai`) |

### `model_pricing` table

| Column | Type |
|--------|------|
| model_id | TEXT | e.g. `qwen3.7-max` |
| display_name | TEXT | e.g. `Qwen3.7 Max` |
| input_cost_per_million | TEXT | e.g. `"0.78"` |
| output_cost_per_million | TEXT | e.g. `"3.90"` |
| cache_read_cost_per_million | TEXT |
| cache_creation_cost_per_million | TEXT |

### `provider_endpoints` table

| Column | Type |
|--------|------|
| id | INTEGER |
| provider_id | TEXT | References providers.id |
| app_type | TEXT |
| url | TEXT | The API endpoint URL |
| added_at | INTEGER |

### `provider_health` table

Tracks connection test results. CC Switch auto-populates on speed test.

### `proxy_config` table

| Column | Description |
|--------|-------------|
| app_type | `claude`, `codex`, `gemini` |
| listen_port | Usually `15721` |
| enabled | 1 for active |

## Provider Settings Config Format

### For OpenAI-compatible API (`apiFormat: "openai"`):

```json
{
  "env": {
    "OPENAI_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "OPENAI_API_KEY": "sk-...",
    "OPENAI_MODEL": "qwen3.7-max",
    "ANTHROPIC_MODEL": "qwen3.7-max"
  },
  "includeCoAuthoredBy": false
}
```

### For Anthropic-compatible API (`apiFormat: "anthropic"`):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-...",
    "ANTHROPIC_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash"
  },
  "includeCoAuthoredBy": false
}
```

## Meta Config Format

```json
{
  "commonConfigEnabled": true,
  "usage_script": {
    "enabled": true,
    "language": "javascript",
    "code": "",
    "timeout": 10,
    "templateType": "balance",
    "autoQueryInterval": 5
  },
  "endpointAutoSelect": true,
  "apiFormat": "openai"
}
```

## Steps to Add a Provider

### 1. Check existing providers

```python
import sqlite3, json
db_path = r"C:\Users\Windows\.cc-switch\cc-switch.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT * FROM providers")
# inspect columns/rows
conn.close()
```

### 2. Generate UUID and timestamp

```python
import uuid, time
new_id = str(uuid.uuid4())
now_ms = int(time.time() * 1000)
```

### 3. Insert provider

```python
cursor.execute("""
    INSERT INTO providers (id, app_type, name, settings_config, website_url, category, 
                           created_at, sort_index, notes, icon, icon_color, meta, 
                           is_current, in_failover_queue, cost_multiplier, 
                           limit_daily_usd, limit_monthly_usd, provider_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    new_id, "claude", "My Provider",
    json.dumps(settings_config), "https://...", "cn_official",
    now_ms, None, None, None, "#FF6A00",
    json.dumps(meta), 0, 0, "1.0", None, None, None
))
```

### 4. Add model pricing (optional)

```python
cursor.execute("""
    INSERT INTO model_pricing (model_id, display_name, input_cost_per_million, 
                               output_cost_per_million, cache_read_cost_per_million, 
                               cache_creation_cost_per_million)
    VALUES (?, ?, ?, ?, ?, ?)
""", ("model-id", "Display Name", "0.78", "3.90", "0", "0"))
```

### 5. Add endpoint

```python
cursor.execute("SELECT MAX(id) FROM provider_endpoints")
max_id = cursor.fetchone()[0] or 0
cursor.execute("""
    INSERT INTO provider_endpoints (id, provider_id, app_type, url, added_at)
    VALUES (?, ?, ?, ?, ?)
""", (max_id + 1, new_id, "claude", base_url, now_ms))
```

### 6. Commit and restart

```python
conn.commit()
conn.close()
```

Then restart CC Switch:
```bash
taskkill //F //IM "cc-switch.exe"
# Wait a moment
start "" "C:\Users\Windows\AppData\Local\Programs\CC Switch\cc-switch.exe"
```

## Querying API for Available Models

To find model IDs available on an OpenAI-compatible endpoint:

```bash
curl -sk "https://dashscope.aliyuncs.com/compatible-mode/v1/models" \
  -H "Authorization: Bearer sk-..."
```

## API Format Compatibility — CRITICAL HARD LIMITATION

CC Switch's proxy for each `app_type` only works with specific API formats:

| app_type | Supported format | Works with |
|----------|-----------------|------------|
| `claude` | **Anthropic only** (`/v1/messages`) | DeepSeek `/anthropic` endpoint, official Anthropic |
| `codex` | **OpenAI** (`/v1/chat/completions`) | Qwen, DeepSeek V4, OpenAI, etc. |
| `gemini` | **Google Gemini** format | Google Gemini API |

### The `apiFormat: "openai"` Trap

**You CANNOT use an OpenAI-compatible API (like Qwen/DashScope) as a `claude` provider.** This is a hard limitation — there is no workaround via database manipulation.

Trying `apiFormat: "openai"` on a `claude` provider causes the proxy to fail with:
```
配置错误: Claude Provider 缺少 base_url 配置
```

Even if you also set `ANTHROPIC_BASE_URL` alongside `OPENAI_BASE_URL`, the proxy will:
- With `apiFormat: "anthropic"` → forward to `ANTHROPIC_BASE_URL/v1/messages` (Anthropic format) — Qwen returns 404 because it doesn't speak Anthropic
- With `apiFormat: "openai"` → the proxy can't find a base_url and returns the proxy_error

The claude proxy code path for OpenAI format **is not implemented** in CC Switch. The proxy doesn't translate between Anthropic and OpenAI formats.

### For Claude Code via VS Code Extension

The VS Code extension (`anthropic.claude-code-*`) reads only `ANTHROPIC_BASE_URL` from `settings.json` env vars. `OPENAI_BASE_URL` is NOT recognized by the Anthropic API client in the extension. Even setting `ANTHROPIC_BASE_URL` to an OpenAI-compatible endpoint won't work because Claude Code sends Anthropic-format `POST /v1/messages` requests, and OpenAI-only APIs don't understand that path or message format.

### What DOES Work

1. **For Anthropic-compatible APIs** (like DeepSeek's `/anthropic` endpoint): Use `app_type=claude` with `apiFormat: "anthropic"` and `ANTHROPIC_*` env vars. This is fully supported.

2. **For OpenAI-compatible APIs** (like Qwen/DashScope): Use `app_type=codex`. CC Switch's codex proxy natively speaks OpenAI format.

3. **Using Qwen with Claude Code directly** (bypassing CC Switch): Requires a **translation proxy** (e.g., LiteLLM, One API, or a custom Python script) that converts Anthropic `POST /v1/messages` requests to OpenAI `POST /v1/chat/completions` format and back. Setting env vars in `~/.claude/settings.json` alone is insufficient because the formats are fundamentally incompatible.

## Provider Settings Config Formats

### For `app_type=claude` (Anthropic format):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-...",
    "ANTHROPIC_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash"
  },
  "includeCoAuthoredBy": false
}
```

### For `app_type=codex` (OpenAI format):

```json
{
  "auth": {
    "apiKey": "sk-..."
  },
  "config": "{\"baseUrl\":\"https://dashscope.aliyuncs.com/compatible-mode/v1\",\"models\":[\"qwen3.7-max\"]}"
}
```

## Switching Active Provider (settings.json)

After adding a provider to the database, update `C:\\Users\\<user>\\.cc-switch\\settings.json` to activate it:

```json
{
  "currentProviderClaude": "<new-provider-uuid>",
  "currentProviderCodex": "<new-provider-uuid>",
  ...
}
```

Also set `is_current=1` in the `providers` table for the new provider, and `is_current=0` for the old one.

## Managing `proxy_live_backup`

When switching providers, delete the old backup so CC Switch doesn't restore the old config on restart:

```python
cursor.execute("DELETE FROM proxy_live_backup WHERE app_type='claude'")
```

Or create a new backup with the correct config:
```python
new_backup = {
    "permissions": { ... },
    "env": { ... },
    "model": "qwen3.7-max",
    "includeCoAuthoredBy": False
}
cursor.execute("INSERT INTO proxy_live_backup (app_type, original_config, backed_up_at) VALUES (?, ?, ?)",
               ("claude", json.dumps(new_backup), time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())))
```

## Known Pitfalls

### SSL Certificate Mismatch on Workspace-Specific URLs

Alibaba Cloud Bailian workspace URLs (e.g., `ws-ugdlgitzrrtmq5x7.cn-beijing.maas.aliyuncs.com`) use internal load balancer SSL certificates that don't match the hostname. **CC Switch validates SSL certificates** and will fail with `SEC_E_WRONG_PRINCIPAL`.

**Fix:** Use the standard `dashscope.aliyuncs.com` domain instead:
- `https://dashscope.aliyuncs.com/compatible-mode/v1` for OpenAI-compatible
- The API key works globally across all DashScope endpoints

The workspace-specific endpoint (`ws-*.maas.aliyuncs.com`) works with `curl -sk` but NOT with CC Switch because CC Switch enforces SSL verification.

### Restart Required

Direct database edits only take effect after restarting CC Switch. Use `taskkill //F //IM "cc-switch.exe"` and relaunch.

**Important:** On restart, CC Switch restores `proxy_live_backup` — which may contain OLD provider config (auth tokens, base URL). You must also delete or update the backup:
```python
cursor.execute("DELETE FROM proxy_live_backup WHERE app_type='claude'")
```
Otherwise the old config persists and your changes are silently overwritten when CC Switch re-takes over the proxy.

### `proxy_live_backup` Persistence

When CC Switch "takes over" (接管) a proxy, it:
1. Backs up the original config to `proxy_live_backup`
2. Writes the provider's env vars to `~/.claude/settings.json`
3. On next restart, restores from backup

If you switch providers via database edit, the old `proxy_live_backup` will be restored on restart, overwriting your changes. Always delete or update the backup after switching.

The backup also preserves OLD auth tokens — if you deleted a provider but the backup still references its token, the token will be restored. Always verify `ANTHROPIC_AUTH_TOKEN` / `OPENAI_API_KEY` after switching.

### Speed Test

CC Switch's built-in speed test sends a test request to the provider. It will fail if:
- SSL certificate is invalid/mismatched
- The API format is wrong (Anthropic vs OpenAI)
- The base URL is incorrect
- The model doesn't exist on that workspace
