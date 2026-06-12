---
name: qwen-anthropic-translation-proxy
description: >-
  Set up a local Python translation proxy that converts Anthropic API format
  (Claude Code) to OpenAI API format (Qwen/DashScope). Use when Qwen doesn't
  support Anthropic API and you need to use it with Claude Code.
---

# Qwen ↔ Anthropic Translation Proxy

When Qwen only supports OpenAI API format but Claude Code speaks Anthropic API, use this proxy.

## Setup

1. Save `qwen-proxy.py` script (see below) to a permanent location, e.g. `D:\Hermes\qwen-proxy.py`

2. Start the proxy:
```bash
python D:\Hermes\qwen-proxy.py &
```

3. Update Claude Code `settings.json` (`~/.claude/settings.json`):
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:15722",
    "ANTHROPIC_AUTH_TOKEN": "sk-your-qwen-api-key",
    "ANTHROPIC_MODEL": "qwen3.7-max"
  }
}
```

4. Update the script's config section with your API key and model:
```python
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
API_KEY = "sk-your-qwen-api-key"
MODEL = "qwen3.7-max"
```

5. Also disable CC Switch claude proxy takeover to prevent overwrites:
```sql
UPDATE proxy_config SET proxy_enabled=0, enabled=0 WHERE app_type='claude';
DELETE FROM proxy_live_backup WHERE app_type='claude';
```
Then restart CC Switch.

## How It Works

The proxy:
- Listens on `127.0.0.1:15722`
- Accepts Anthropic `POST /v1/messages` requests
- Translates to OpenAI `POST /v1/chat/completions` format
- Forwards to Qwen/DashScope
- Translates OpenAI response back to Anthropic format
- Supports both streaming and non-streaming modes

## Translation Details

| Anthropic | OpenAI |
|-----------|--------|
| `system` field | First message with `role: "system"` |
| `messages[].content` as text or blocks | `messages[].content` as text or array |
| Image blocks (`type: "image"`, `source: {type: "base64"}`) | `image_url` with base64 data URL |
| SSE streaming with `content_block_delta` events | SSE streaming with `choices[].delta.content` |
| `stop_reason: "end_turn"` | `finish_reason: "stop"` |
| `stop_reason: "max_tokens"` | `finish_reason: "length"` |

## Testing the Proxy

```bash
curl -s "http://127.0.0.1:15722/v1/messages" \
  -H "x-api-key: sk-your-api-key" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.7-max","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

## Script Location

D:\Hermes\qwen-proxy.py
