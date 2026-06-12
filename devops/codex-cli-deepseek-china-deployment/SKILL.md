---
name: codex-cli-deepseek-china-deployment
description: Analyze and deploy coding agents with DeepSeek V4 in China. Covers Codex CLI protocol incompatibility (Responses API vs Chat Completions API), and recommends alternatives like OpenCode, Claude Code + cc-switch, or Aider.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Codex-CLI, DeepSeek, China, Coding-Agent, OpenCode, Aider]
    related_skills: [opencode, claude-code, cc-switch-model-routing]
---

# Codex CLI + DeepSeek V4 in China — Deployment Analysis

## Key Finding: Protocol Incompatibility

**Codex CLI v0.136.0+ no longer supports the Chat Completions API.** OpenAI explicitly removed `wire_api = "chat"` support. Codex CLI now exclusively speaks the **Responses API** (`/v1/responses`).

DeepSeek V4 (and most third-party providers) only support the **Chat Completions API** (`/v1/chat/completions`).

This means **Codex CLI cannot directly use DeepSeek V4** — they speak different wire protocols.

Evidence from source code (`codex-rs/model-provider-info/src/lib.rs`):
```rust
const CHAT_WIRE_API_REMOVED_ERROR: &str = "`wire_api = \"chat\"` is no longer supported.\nHow to fix: set `wire_api = \"responses\"` in your provider config.\nMore info: https://github.com/openai/codex/discussions/7782";
```

## Codex CLI Architecture (npm → Rust Binary)

Codex CLI is packaged as an npm package (`@openai/codex`) but the actual logic is a Rust binary.

**npm wrapper** (`codex-cli/bin/codex.js`):
- Detects platform (win32-x64, darwin-arm64, etc.)
- Resolves platform-specific Rust binary package (e.g. `@openai/codex-win32-x64`)
- Spawns the native Rust binary with environment forwarded

**Rust binary** (`codex-rs/`):
- Config handling: `codex-rs/config/src/config_toml.rs`
- Model provider info: `codex-rs/model-provider-info/src/lib.rs`
- Provider implementation: `codex-rs/model-provider/src/provider.rs`
- Platform packages: `@openai/codex-win32-x64` etc. (~10.8 kB npm, Rust binary bundled inside)

**Config file**: `~/.codex/config.toml` (TOML format, NOT YAML)

Key fields in config.toml:
```toml
model = "deepseek-v4-flash"           # Model override
model_provider = "custom-deepseek"    # Provider key from [model_providers] table
model_context_window = 128000         # Optional context window override

[model_providers.custom-deepseek]
name = "DeepSeek V4"
base_url = "https://api.deepseek.com"
env_key = "DEEPSEEK_API_KEY"         # Reads from env var
wire_api = "responses"                # NOW ONLY "responses" - "chat" was REMOVED
```

**Key source files for debugging config/provider issues:**
- `codex-rs/config/src/config_toml.rs` — All config.toml types
- `codex-rs/model-provider-info/src/lib.rs` — `ModelProviderInfo` struct, provider registry
- `codex-rs/model-provider/src/provider.rs` — `ModelProvider` trait, `create_model_provider()`
- `codex-rs/model-provider/src/models_endpoint.rs` — `/models` endpoint client

## Investigation Methodology

To verify protocol support for any coding agent:

1. Check the agent's provider configuration source code on GitHub
2. Look for `WireApi`, `wire_api`, `base_url`, `env_key` in model-provider code
3. Check the `ModelProviderInfo` struct for `base_url`, `wire_api` fields
4. Verify whether the provider supports `chat` or `responses` protocol variants
5. For Codex CLI specifically, check `codex-rs/model-provider-info/src/lib.rs` and `codex-rs/config/src/config_toml.rs`

## Recommended Solutions for DeepSeek V4 in China

### Option 1: OpenCode (Best Alternative to Codex CLI)

OpenCode is provider-agnostic and natively supports `OPENAI_BASE_URL` with Chat Completions API.

```
npm i -g opencode-ai@latest
set OPENAI_BASE_URL=https://api.deepseek.com/v1
set OPENAI_API_KEY=sk-<key>
set OPENAI_MODEL=deepseek-v4-flash
opencode run 'task description'
```

Key flags for OpenCode:
- `opencode run 'prompt'` — one-shot execution, no pty needed
- `--thinking` — show model reasoning
- `--model provider/model` — force specific model
- `-f file` — attach context files

### Option 2: Continue Using Claude Code + cc-switch

If user already has Claude Code + cc-switch proxy routing to DeepSeek, this is already stable. The cc-switch proxy translates between Claude Code's protocol and DeepSeek's Chat Completions API.

### Option 3: Aider + DeepSeek V4

```
pip install aider
aider --model deepseek-v4-flash --openai-api-key sk-<key>
```

- Python-based, excellent git integration
- Pure terminal interaction (no TUI)
- DeepSeek model ID format: `deepseek-v4-flash` or `deepseek-v4-pro`

### Option 4: Translation Proxy (Not Recommended)

Building a local proxy to convert Responses API → Chat Completions API is possible but:
- Requires deep understanding of both protocols
- Codex CLI updates frequently — protocol changes break the proxy
- High maintenance burden for little benefit over OpenCode

## Deployment Context for China

- DeepSeek API (`api.deepseek.com`) is directly accessible from mainland China with low latency
- No VPN or proxy needed for DeepSeek API access
- Node.js/npm packages may need registry mirror: `npm config set registry https://registry.npmmirror.com`
- Python packages may need: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`

## Pitfalls

- **Do NOT assume OpenAI-compatible = works with Codex CLI.** Codex CLI exclusively uses Responses API, not Chat Completions API.
- **Codex CLI's `~/.codex/config.toml` `model_providers` section** allows custom providers with `base_url` and `env_key`, but the `wire_api` is hardcoded to `responses` now.
- **Ollama provider** in Codex CLI requires Ollama v0.13.4+ for Responses API support.
- **DeepSeek V4 model IDs**: Flash is `deepseek-v4-flash`, Pro is `deepseek-v4-pro`. Verify with `GET {base_url}/v1/models` with API key in Authorization header.
