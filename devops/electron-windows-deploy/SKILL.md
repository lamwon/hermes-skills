---
name: electron-windows-deploy
description: Deploy an Electron app on Windows without Visual Studio Build Tools — handles native module prebuilt binaries, Electron binary download from Chinese mirrors, and manual module registration.
---

# Deploy Electron App on Windows (No VS Build Tools)

## Problem

Running `npm install` on an Electron project fails on Windows due to:
1. **Native modules** (e.g., `better-sqlite3`) require `node-gyp` + Visual Studio C++ Build Tools
2. **Electron binary** download from GitHub is slow/unreachable from China
3. `postinstall` scripts fail, leaving the module in an inconsistent state

## Prerequisites

- Node.js + npm installed
- `curl`, `unzip` available (Git Bash on Windows)
- No Visual Studio Build Tools required

## Step-by-Step

### 1. Install dependencies without scripts

```bash
cd /path/to/electron-app
npm install --ignore-scripts
```

This skips all `postinstall` hooks that try to download binaries or compile native modules.

### 2. Handle native modules (better-sqlite3 pattern)

Check which native modules need prebuilt binaries:

```bash
# Find modules that failed during normal install
ls node_modules/ | xargs -I{} grep -l '"postinstall"' node_modules/{}/package.json 2>/dev/null
```

For `better-sqlite3` specifically:

#### 2a. Determine Electron's ABI version

```bash
# After installing electron module, check ABI
cat node_modules/electron/abi_version
# Returns e.g. "140" for Electron 39
```

#### 2b. Find matching prebuilt binary

Check WiseLibs/better-sqlite3 releases for the right ABI:
- Visit: https://github.com/WiseLibs/better-sqlite3/releases
- Look for: `better-sqlite3-v12.x.x-electron-v{ABI}-win32-x64.tar.gz`
- Must match the ABI version from step 2a, NOT Node.js's ABI

#### 2b-opt. Programmatic search (faster than browsing releases)

```python
import urllib.request, json, re

url = "https://api.github.com/repos/WiseLibs/better-sqlite3/releases?per_page=20"
req = urllib.request.Request(url, headers={"User-Agent": "script/1.0"})
resp = urllib.request.urlopen(req, timeout=15)
releases = json.loads(resp.read())

target_abi = 140  # from electron/abi_version
pkg_ver = "12.8.0"  # from package.json

for rel in releases:
    for asset in rel.get('assets', []):
        name = asset['name']
        m = re.search(rf'better-sqlite3-v{re.escape(pkg_ver)}-electron-v({target_abi})-win32-x64\.tar\.gz', name)
        if m:
            print(f"Found: {asset['browser_download_url']}")
            print(f"Size: {asset['size']} bytes")
```

#### 2c. Download and extract

```bash
# Download the correct ABI version
curl -L -o /tmp/bs3.tar.gz \
  "https://github.com/WiseLibs/better-sqlite3/releases/download/v12.8.0/better-sqlite3-v12.8.0-electron-v140-win32-x64.tar.gz"

# Extract into the module directory
mkdir -p node_modules/better-sqlite3/build/Release
tar -xzf /tmp/bs3.tar.gz -C node_modules/better-sqlite3/

# Verify
ls -lh node_modules/better-sqlite3/build/Release/better_sqlite3.node
# Should show ~1.9MB file
```

### 3. Handle Electron binary

#### 3a. In China: use npmmirror.com

```bash
# Set mirror and run install script
ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/" \
  node node_modules/electron/install.js

# Or download manually
curl -L -o /tmp/electron.zip \
  "https://npmmirror.com/mirrors/electron/39.2.6/electron-v39.2.6-win32-x64.zip"
unzip -o /tmp/electron.zip -d node_modules/electron/dist/
```

#### 3b. Create path.txt (required if postinstall was skipped)

The `electron` package's `index.js` reads `path.txt` to find the binary:

```bash
# Create the file (NO trailing newline)
echo -n "electron.exe" > node_modules/electron/path.txt
```

Verify Electron path resolution:

```bash
node -e "console.log('Electron:', require('electron'))"
# Should output: D:\path\to\node_modules\electron\dist\electron.exe
```

### 4. Verify

```bash
# Test better-sqlite3 loading (under Electron, not system Node.js)
node -e "
const b = require('better-sqlite3');
const db = new b(':memory:');
db.exec('CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)');
db.exec('INSERT INTO t VALUES (1, \"hello\")');
const row = db.prepare('SELECT * FROM t').get();
console.log('SQLite OK:', JSON.stringify(row));
db.close();
"

# Start the app in dev mode
npm run dev
```

### 5. Build for distribution

```bash
ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/" npm run build:win
```

## Pitfalls

- **ABI mismatch**: The native module MUST match Electron's ABI (from `node_modules/electron/abi_version`), NOT system Node.js's ABI. Using the wrong ABI gives: `was compiled against a different Node.js version using NODE_MODULE_VERSION X. This version of Node.js requires NODE_MODULE_VERSION Y.`
- **path.txt without newline**: The file must contain ONLY `electron.exe` — no trailing `\n` or `\r\n`. `echo -n` is required.
- **Cache errors on first run**: `Unable to create cache` / `Gpu Cache Creation failed` warnings are harmless on first Electron launch.
- **EBUSY errors during npm install**: If a previous install left files in a bad state, try deleting `node_modules/electron` with `rd /s /q node_modules\electron` (Windows) before retrying.
- **Port conflicts**: `electron-vite dev` may use ports 5173/5174. If one is in use, it automatically tries the next.
- **npm cleanup can destroy manual work**: When running `npm install` after manually placing native binaries, npm's cleanup phase may try to remove and reinstall the module. Use `--ignore-scripts` upfront to prevent this.

## Verification checklist

- [ ] `npm install --ignore-scripts` completed without errors
- [ ] All native `.node` binaries placed in correct `build/Release/` directories
- [ ] Electron `abi_version` matches the prebuilt binary's Electron AB
- [ ] `path.txt` exists with correct content (no trailing newline)
- [ ] `node -e "require('electron')"` returns valid path
- [ ] `npm run dev` starts without crashing
