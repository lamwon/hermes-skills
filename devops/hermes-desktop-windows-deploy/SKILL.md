---
name: hermes-desktop-windows-deploy
description: Deploy fathah/hermes-desktop (Electron/React companion app for Hermes Agent) on Windows with a portable Hermes Agent installation. Covers native module fixes, Electron binary setup, and directory structure compatibility.
---

# Hermes Desktop Windows Deployment

Deploy [fathah/hermes-desktop](https://github.com/fathah/hermes-desktop) on Windows when Hermes Agent is installed as a portable package (not the standard `install.ps1` layout).

## Prerequisites

- Node.js (v26 works, though the package may warn about engine mismatch)
- Git
- Existing Hermes Agent installation (e.g., at `D:\\Hermes\\portable-hermes-agent\\`)
- Hermes config at `~/.hermes/config.yaml`

## Step 1: Clone

```bash
cd /d/Hermes
git clone https://github.com/fathah/hermes-desktop.git
cd hermes-desktop
```

## Step 2: Install dependencies (with native module workaround)

`better-sqlite3` is a native module that needs a prebuilt binary matching your Electron version. On Windows without VS Build Tools, node-gyp compilation will fail.

### 2a. Install with ignore-scripts first

```bash
npm install --ignore-scripts
```

### 2b. Determine Electron ABI version

```bash
cat node_modules/electron/abi_version
```

This returns a number like `140` for Electron 39.

### 2c. Download matching prebuilt better-sqlite3 binary

Check available releases at: https://api.github.com/repos/WiseLibs/better-sqlite3/releases

Find a binary matching your project's `better-sqlite3` version AND the Electron ABI version (e.g., `electron-v140` for Electron 39).

```bash
curl -L -o /tmp/bs3.tar.gz "https://github.com/WiseLibs/better-sqlite3/releases/download/v12.8.0/better-sqlite3-v12.8.0-electron-v140-win32-x64.tar.gz"
mkdir -p node_modules/better-sqlite3/build/Release
tar -xzf /tmp/bs3.tar.gz -C node_modules/better-sqlite3/
```

### 2d. Set up Electron binary

Create `path.txt` in the electron module so it can find the binary:

```bash
echo -n "electron.exe" > node_modules/electron/path.txt
```

Download Electron binary from Chinese mirror for faster speeds:

```bash
curl -L -o /tmp/electron.zip "https://npmmirror.com/mirrors/electron/39.2.6/electron-v39.2.6-win32-x64.zip"
unzip -o /tmp/electron.zip -d node_modules/electron/dist/
```

Verify:

```bash
node -e "try { console.log('Electron path:', require('electron')); } catch(e) { console.log('Error:', e.message); }"
```

## Step 3: Fix portable Hermes Agent detection

Hermes Desktop expects the directory structure:
```
{HERMES_HOME}/hermes-agent/venv/Scripts/pythonw.exe
{HERMES_HOME}/hermes-agent/venv/Scripts/hermes.exe
```

But portable installations have the agent code and embedded Python elsewhere (e.g., `D:\\Hermes\\portable-hermes-agent\\`).

**CRITICAL: Do NOT copy `pythonw.exe` to a different directory.** The embedded Python binary needs its stdlib (`python313.zip`, `Lib/`, `DLLs/`) in the same directory as the exe. Copying it causes `Fatal Python error: Failed to import encodings` when CWD differs from the exe directory.

### Correct approach: Junction `venv/Scripts` to the entire `python_embedded`

Make `venv/Scripts` point to the full `python_embedded` directory via NTFS junction.

#### 3a. Clean old venv (if previously set up with broken approach)

```bash
rm -rf {HERMES_HOME}/hermes-agent/venv
```

#### 3b. Create `venv/Scripts` as junction to `python_embedded`

Run this from **cmd.exe** (not PowerShell, not Git Bash):

```batch
mklink /J "{HERMES_HOME}\hermes-agent\venv\Scripts" "D:\Hermes\portable-hermes-agent\python_embedded"
```

This makes everything in `python_embedded` accessible as if it were in `venv/Scripts`.

#### 3c. Copy `hermes.exe` into the junction root

The desktop checks for `venv/Scripts/hermes.exe`. Through the junction this resolves to `python_embedded/hermes.exe`, but the real file is at `python_embedded/Scripts/hermes.exe`. Copy it there:

```bash
cp /d/Hermes/portable-hermes-agent/python_embedded/Scripts/hermes.exe /d/Hermes/portable-hermes-agent/python_embedded/hermes.exe
```

#### 3d. Verify

From any working directory:

```bash
cd /d/Hermes/hermes-agent
venv/Scripts/pythonw.exe -m hermes_cli.main --version
```

Expected output:
```
Hermes Agent v0.5.0 (2026.3.28)
Project: D:\Hermes\portable-hermes-agent
Python: 3.13.12
```

#### How the junction resolves paths

| Desktop expects | Resolves via junction to |
|---|---|
| `venv/Scripts/pythonw.exe` | `python_embedded/pythonw.exe` ✓ |
| `venv/Scripts/python313.zip` | `python_embedded/python313.zip` ✓ |
| `venv/Scripts/Lib/` | `python_embedded/Lib/` ✓ |
| `venv/Scripts/DLLs/` | `python_embedded/DLLs/` ✓ |
| `venv/Scripts/hermes.exe` | `python_embedded/hermes.exe` (copied in 3c) ✓ |

The original `python313._pth` with relative paths (`Lib`, `DLLs`, `.`) works because all stdlib files are in the junction-visible directory.

### 3e. Set working directory in desktop config

```bash
echo '{"locale": "en", "lastCwd": "D:\\"}' > ~/.hermes/desktop.json
```

## Step 4: Run

```bash
cd /d/Hermes/hermes-desktop
npm run dev
```

## Pitfalls

### CRLF line endings in config.yaml break provider detection

Hermes Desktop uses regex-based YAML parsing in `config.ts` (`readTopLevelBlock`). When `config.yaml` has Windows CRLF (`\r\n`) line endings, the `\r` character is included in parsed values. This causes:

- `"custom\r"` ≠ `"custom"` → `providerDoesNotNeedApiKey()` returns `false`
- `hasApiKey` stays `false` → Desktop shows "API没有接入" (Setup screen) even though config is valid

**Fix:** Convert `config.yaml` to LF line endings:
```python
with open("~/.hermes/config.yaml", 'rb') as f:
    raw = f.read()
with open("~/.hermes/config.yaml", 'wb') as f:
    f.write(raw.replace(b'\r\n', b'\n'))
```

**Detection:** Check the file with `xxd ~/.hermes/config.yaml | head`. If lines end with `0d 0a` (CRLF), you have this bug. Healthy file ends with `0a` (LF).

### `configured` vs `hasApiKey` distinction in App.tsx

The app's startup flow (`App.tsx` line 60-68) has three states:
1. `!installed` → **Welcome** screen (install Hermes first)
2. `installed && !hasApiKey` → **Setup** screen ("API没有接入")
3. `installed && hasApiKey` → **Main** screen (chat)

If you see "Setup" screen despite having a valid config.yaml, the issue is either:
- CRLF line endings (see above) → value comparison fails
- `provider` in config.yaml is not in `PROVIDERS_WITHOUT_API_KEYS` set in `providers.ts`
- No `.env` or `auth.json` file exists (if provider needs explicit key)

### Health check fails with "Hermes is installed, but a health check didn't complete"

This appears when `verifyInstall()` in `installer.ts` fails. It runs `pythonw.exe -m hermes_cli.main --version` with a 15-second timeout. Common causes:

1. **venv/Scripts doesn't exist** — fix with Step 3 junction approach above
2. **Copied pythonw.exe without stdlib** — using the junction approach (not copying) avoids this
3. **CRLF in python313._pth** — the `._pth` file parser includes `\r` in paths, causing "Failed to import encodings"
4. **PATH or env conflicts** — `PIP_TARGET`, `PIP_PREFIX`, `PYTHONPATH` env vars can interfere with Python's startup

### Chat fails with "Error: Hermes exited with code 3221225781"

The error code **3221225781** = **0xC0000135** = **STATUS_DLL_NOT_FOUND**. This means Windows can't find a required DLL when launching `pythonw.exe`.

This happens even after the health check warning is dismissed — the Desktop falls back to `sendMessageViaCli()` (spawning `pythonw.exe -m hermes_cli.main`) instead of the HTTP API path, and the spawned process crashes immediately.

**Check your HERMES_HOME:** The Desktop may use a DIFFERENT location than expected. The resolution order is:
1. `process.env.HERMES_HOME` (often NOT set when launched from Start Menu)
2. `readHermesHomeOverride()` (Electron userData/hermes-home.json)
3. `defaultHermesHome()` → probes `%LOCALAPPDATA%\hermes` first, then `~\.hermes`

If the user has config at both `D:\Hermes\` and `C:\Users\Windows\.hermes\`, the Desktop likely uses **`C:\Users\Windows\.hermes\`** because `defaultHermesHome()` finds config.yaml there first.

**Fix:** Apply the junction approach to ALL potential HERMES_HOME locations:

```bash
# Check which one is active
ls ~/.hermes/hermes-agent/venv/Scripts/
ls /c/Users/Windows/AppData/Local/hermes/hermes-agent/venv/Scripts/

# Fix the active one by replacing venv/Scripts with junction to python_embedded
cmd /c "mklink /J \"C:\Users\Windows\.hermes\hermes-agent\venv\Scripts\" \"D:\Hermes\portable-hermes-agent\python_embedded\""
```

Verify the fix works:
```bash
cd ~/.hermes/hermes-agent
venv/Scripts/pythonw.exe -m hermes_cli.main --version
# Should output version info, not DLL error
```

### "Hermes is not installed" in the app

The desktop checks `existsSync(HERMES_PYTHON) && existsSync(HERMES_SCRIPT)` where:
- `HERMES_PYTHON` = `{HERMES_HOME}/hermes-agent/venv/Scripts/pythonw.exe`
- `HERMES_SCRIPT` = `{HERMES_HOME}/hermes-agent/venv/Scripts/hermes.exe`

Ensure both files exist (Step 3). If using a portable install, the entire `venv/` subtree must be set up via the junction approach.

### npm install fails on better-sqlite3 postinstall

Use `--ignore-scripts` and manually place the prebuilt binary (Steps 2a-2c).

### Directory junction creation fails

Run the batch file directly from an Administrator cmd.exe prompt if "Access denied" occurs. Junctions are essential for the portable Hermes install to work with the desktop app.
