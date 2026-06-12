---
name: claude-code-vscode-auto-confirm
description: Bypass all permission confirmation prompts in Claude Code when running as a VS Code extension (anthropic.claude-code). The VS Code extension has its own safety gate separate from ~/.claude/settings.json.
---

# Claude Code VS Code Extension - Auto-Confirm Setup

## Problem

Claude Code keeps showing confirmation dialogs (bash, edit, write, etc.) even after setting `permissions.defaultMode: "bypassPermissions"` in `~/.claude/settings.json`.

## Root Cause

The VS Code extension `anthropic.claude-code` has its **own permission management layer** that runs BEFORE the CLI's internal permission system. It stores the permission mode in VS Code's `globalState` and passes `--permission-mode` to the CLI as a launch flag, **overriding** whatever is in `~/.claude/settings.json`.

The extension source code (v2.1.128) reveals a **three-setting chain**:

### Setting 1: `claudeCode.initialPermissionMode` (VS Code config)

The extension's `getInitialPermissionMode()` in the extension JS reads:

1. VS Code setting `claudeCode.initialPermissionMode` → first priority
2. `globalState.get("defaultPermissionMode")` → set when user changes mode in UI
3. Falls back to `"default"`

**If this resolves to `"default"`, the extension passes `--permission-mode default` to the CLI, overriding `~/.claude/settings.json`.**

### Setting 2: `claudeCode.allowDangerouslySkipPermissions` (safety gate)

Even if `initialPermissionMode` is `"bypassPermissions"`, the extension has a safety gate:

```javascript
getInitialPermissionMode() {
    let V = workspace.getConfiguration("claudeCode").inspect("initialPermissionMode"),
        K = V?.workspaceFolderValue ?? V?.workspaceValue ?? V?.globalValue,
        B = this.context.globalState.get("defaultPermissionMode"),
        N = K || B || "default";
    if (N === "bypassPermissions" && !this.getAllowDangerouslySkipPermissions())
        return "default";  // <-- downgrades back to default!
    return N;
}

getAllowDangerouslySkipPermissions() {
    return workspace.getConfiguration("claudeCode").get("allowDangerouslySkipPermissions") || false;
}
```

Without `claudeCode.allowDangerouslySkipPermissions: true`, the safety gate overrides `bypassPermissions` back to `default`.

### Setting 3: `~/.claude/settings.json` (CLI config)

The CLI itself reads `permissions.defaultMode` as a fallback — but only if the extension doesn't pass `--permission-mode`. Since the extension always passes it, this file is effectively **overridden** when the extension's resolution produces `"default"`.

## Fix

**Three** settings are needed — **all three must be set**:

### 1. VS Code settings.json (extension-level initial mode)
Add to `~/AppData/Roaming/Code/User/settings.json` (Windows) or `~/.config/Code/User/settings.json` (Linux/Mac):

```json
{
    "claudeCode.allowDangerouslySkipPermissions": true,
    "claudeCode.initialPermissionMode": "bypassPermissions",
    ...
}
```

- `allowDangerouslySkipPermissions` — the **safety gate** that must be explicitly opted into
- `initialPermissionMode` — tells the extension's **own** permission resolver to use `bypassPermissions` instead of `default`

### 2. `~/.claude/settings.json`
Keep the existing permissions config (used as fallback):

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions",
    "allow": [
      "Read", "Edit", "Write", "PowerShell",
      "Glob", "Grep", "Agent", ...
    ]
  },
  ...
}
```

### Troubleshooting: still seeing prompts?

If dialogs persist despite all three settings:

1. **Restart VS Code completely** (or `Ctrl+Shift+P` → `Developer: Reload Window`) — settings are read at extension activation time
2. **Check for workspace overrides**: `your-project/.vscode/settings.json` can override `claudeCode.*` settings
3. **Verify the extension reads correctly** — open VS Code Developer Tools (Help → Toggle Developer Tools) and check the Console for any errors loading the permission configuration

## What NOT to do (fake env vars)

These environment variables **do not exist** and have no effect on Claude Code:

- `CLAUDE_CODE_AUTO_CONFIRM` — **fake**, not recognized
- `CLAUDE_CODE_DANGEROUSLY_SKIP_PERMISSIONS` — **fake**, not recognized

Verified by examining `claude --help` output (v2.1.126+). The only valid CLI flags are:
- `--permission-mode bypassPermissions`
- `--allow-dangerously-skip-permissions` (CLI flag, not env var)
- `--dangerously-skip-permissions` (CLI flag, not env var)

## Verification

After adding both settings, restart VS Code completely (or `Ctrl+Shift+P` → `Developer: Reload Window`). Claude Code should no longer show any confirmation dialogs.

## How to discover this for yourself

If the extension version changes and the setting name changes, you can find it by examining the extension source:

```bash
# Find the extension directory
ls ~/.vscode/extensions/anthropic.claude-code-*/

# Search for the safety gate
grep -oP 'bypassPermissions.{0,200}' extension.js
# Look for: bypassPermissions && !this.getAllowDangerouslySkipPermissions

# Find the getAllowDangerouslySkipPermissions implementation
grep -oP 'getAllowDangerouslySkipPermissions.{0,200}' extension.js
# Shows it reads from VS Code config: e6("allowDangerouslySkipPermissions")

# Confirm the setting namespace
grep -oP 'allowDangerouslySkipPermissions.{0,150}' extension.js
# Shows it's under "claudeCode" namespace
```
