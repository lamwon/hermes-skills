---
name: windows-c-drive-cleanup
description: Systematic approach to free up space on Windows C drive — scan for space hogs, clean app caches, launch uninstallers, and run system cleanup tools.
---

# Windows C Drive Cleanup

Systematic approach to free up space on a Windows C drive (typically 80-256GB SSD). Combines Python scanning for large directories, cache cleanup, software uninstallation, and system-level cleanup via UAC elevation.

## Trigger

User asks about C drive being full, needing more space, or cleaning up disk.

## Step-by-Step

### 0. Determine Cleanup Phase

Ask what's already been done. If previous cleanup has already happened (caches cleared, uninstallers launched, junctions created), skip to **Step 7 — Deep Investigation**.

### 1. Check Current Free Space

Use Python with `ctypes` to avoid cmd/PowerShell encoding issues. Or use the `run_python` tool which avoids shell escaping issues:

```python
import ctypes
free = ctypes.c_ulonglong(0)
total = ctypes.c_ulonglong(0)
ctypes.windll.kernel32.GetDiskFreeSpaceExW("C:\\", None, ctypes.byref(total), ctypes.byref(free))
free_gb = free.value / (1024**3)
total_gb = total.value / (1024**3)
print(f"Free: {free_gb:.1f} GB / Total: {total_gb:.1f} GB")
```

### 2. Check Low-Hanging Fruit

Check if these are consuming space:
- **Hibernation**: `powercfg -h status` (needs admin). `powercfg -h off` to disable (frees ~RAM size GB)
- **Temp folders**: `%temp%` and `C:\Windows\Temp` — run cleanmgr instead
- **pagefile.sys / hiberfil.sys**: Check if they exist at C:\ root (protected OS files)

### 3. Scan for Space Hogs

Use Python `os.walk` + `os.scandir` to find large directories. Scan these areas:

- `C:\Users\<username>` — user profile (AppData is often the biggest)
- `C:\Program Files` and `C:\Program Files (x86)`
- `C:\Windows` — especially WinSxS

**Important**: The `execute_code` sandbox on Windows **cannot handle Chinese characters** in source code. Use only ASCII/English in Python scripts, or add `# -*- coding: utf-8 -*-` at the top.

**Pitfall**: PowerShell `$_` variable gets mangled by Git Bash's escaping when passed via the terminal tool. Use `execute_code` with Python instead of terminal for anything involving PowerShell with `$_`.

### 4. Clean App Caches (No Admin Needed)

Common cache directories that are safe to delete (apps will recreate them):

- `%APPDATA%\ifonts_client\CoreSync\font` — iFonts/字由 font cache (can be 3-8GB)
- `%APPDATA%\Tencent\xwechat\xplugin` and `\radium` — WeChat web cache
- `%LOCALAPPDATA%\Tencent\QQGuild` — QQ Guild version cache
- `%LOCALAPPDATA%\ima.copilot\User Data\reshub` — Microsoft Copilot resource cache
- `%APPDATA%\Tencent\QQPCMgr` — QQ PC Manager cache
- `%LOCALAPPDATA%\Tencent\qq-play` — QQ game cache
- npm cache: `npm cache clean --force`
- **uv cache**: `uv cache clean` -- commonly 2-3 GB of cached Python packages. uv stores wheels and build artifacts in `%LOCALAPPDATA%\uv\cache`. Safe to clean.
- **npm _npx cache**: `%LOCALAPPDATA%\npm-cache\_npx` can be 0.5-1GB. Delete the _npx folder manually.
- pip cache: `pip cache purge`
- **ms-playwright**: `%LOCALAPPDATA%\ms-playwright` -- chromium browser binaries (~0.4-0.7 GB each). Safe to delete if not actively using Playwright; re-download with `npx playwright install chromium`.

Use `shutil.rmtree(path, ignore_errors=True)` in Python to delete.

### 5. Launch Uninstallers (Needs UAC)

On Windows without admin shell access, use PowerShell's `Start-Process -Verb RunAs` to spawn processes with UAC elevation. The user clicks "Yes" on the UAC prompt.

```python
import subprocess
subprocess.run(["powershell", "-Command", 
    "Start-Process 'C:\\Path\\To\\Uninstall.exe' -Verb RunAs"],
    capture_output=True, timeout=5)
```

**Common software to check for uninstallation:**
- QQNT / Weixin (Tencent) — `C:\Program Files\Tencent\QQNT\Uninstall.exe`
- QQPCMgr / Qzone — check `C:\Program Files (x86)\Tencent\`
- Tesseract-OCR — `C:\Program Files\Tesseract-OCR\tesseract-uninstall.exe`
- JetBrains IDEs — `C:\Program Files\JetBrains\*\bin\Uninstall.exe`
- MS SQL Server LocalDB — via `MsiExec.exe /I{GUID}`
- Huawei BasicService / Hiview — `C:\Program Files\Huawei\*\uninst.exe`

### 6. System Cleanup Tools (Needs UAC)

Launch these with `Start-Process -Verb RunAs`:

- **Disk Cleanup**: `cleanmgr /sageset:2` (opens settings dialog — user checks all boxes), then `cleanmgr /sagerun:2` to execute. Also click "Clean up system files" for Windows Update cleanup.
- **DISM WinSxS**: `DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase` — frees 2-8GB from component store.
- **Programs and Features**: `control appwiz.cpl` — for software that doesn't have standalone uninstallers.

### 7. Deep Investigation (Post-Cleanup)

If basic cleanup, uninstallers, and junction migrations are already done but C drive is still full, scan these commonly overlooked areas:

**Check if previous uninstallers actually completed:**
- `C:\Program Files (x86)\Tencent` — remnants after QQ/WeChat uninstall. Check size.
- `C:\Program Files\Tencent` — QQNT remnants.
- `C:\ProgramData\Autodesk` — if AutoCAD/etc uninstalled, cache remains. ~1+ GB.
- `C:\Program Files (x86)\Microsoft\Edge*` — Edge/EdgeCore/EdgeWebView browser engines. These are system components and CANNOT be removed, but identify them so user understands.

**Check AppData\Local\Programs for portable software:**
This directory contains self-contained apps (no installer). Large items to investigate:
- Python embedded environments (Hermes Agent's `Python311` can be ~3 GB)
- VS Code (0.7-0.8 GB)
- Obsidian, CC Switch, WorkBuddy (often junction points)
- Use `du -sh` on subfolders or Python os.walk to find big ones

**Check Python embedded site-packages (if Hermes Agent is installed):**
- `%LOCALAPPDATA%\Programs\Python\Python311\Lib\site-packages` can be 2.8+ GB
- Largest packages are typically: torch (1.1 GB), PySide6 (0.6 GB), transformers (0.12 GB), scipy (0.12 GB)
- If Hermes doesn't need torch/PySide6 for your usage, these can be pip uninstalled. But be careful -- Hermes may depend on them.

**Check WSL instances:**
```bash
wsl --list --verbose
```
WSL disk images (`ext4.vhdx`) are stored in `%LOCALAPPDATA%\Packages\*\LocalState\` and can be 5-20+ GB.

**Check Docker:**
`%LOCALAPPDATA%\Docker` — images, containers, volumes. Can be 10+ GB.

**Check VS Code extensions (Roaming + Programs + .vscode):**
These three locations combined can be 2-3 GB total:
- `%APPDATA%\Code` (User data + extensions)
- `%LOCALAPPDATA%\Programs\Microsoft VS Code` (VS Code itself)
- `%USERPROFILE%\.vscode` (workspace settings + extension caches)

**Check hidden cache directories:**
- `%LOCALAPPDATA%\Microsoft\Edge` / `EdgeUpdate` — Edge browser cache/code. Can be 1-2 GB.
- `%USERPROFILE%\.cache` — various tool caches (0.2-0.5 GB typical)
- `%USERPROFILE%\.rustup` / `.cargo` — Rust toolchain caches (1-5 GB if installed)

### Scanning Technique

When terminal PowerShell `$_` variable keeps breaking due to Git Bash escaping, write a `.ps1` script to disk via `write_file` and run it with:
```bash
powershell -NoProfile -ExecutionPolicy Bypass -File /tmp/disk_check.ps1
```
This avoids all inline escaping issues. Use `\$_.Sum` or a named variable in ForEach-Object to reference pipeline objects.

## Pitfalls

1. **`execute_code` sandbox encoding**: Python files from the sandbox default to ASCII. If ANY Chinese characters appear in the code (even in comments or f-strings), you get `SyntaxError: Non-UTF-8 code starting with '\x...'`. Solution: use only ASCII characters, or add `# -*- coding: utf-8 -*-` as the first line.

2. **PowerShell `$_` escapability**: When running PowerShell via `terminal()` (which uses Git Bash), the `$_` variable in `Where-Object { $_.PSIsContainer }` gets mangled by Git Bash's variable substitution. Use `execute_code` (Python with subprocess) instead.

3. **UAC elevation is interactive**: `Start-Process -Verb RunAs` launches the process but the user must click through UAC prompts and any subsequent confirmation dialogs. You cannot automate these.

4. **`cleanmgr /sagerun:N` requires pre-configured sageset**: If `/sageset:N` was never run first, `/sagerun:N` does nothing. Use the GUI approach (`/d C:`) instead, or launch `/sageset:2` first for the user to configure.

5. **AppData vs ProgramData**: User-level caches are in `C:\Users\<username>\AppData`. System-level caches in `C:\ProgramData`. Check both.

## Verification

After cleanup, check free space again:
```python
ctypes.windll.kernel32.GetDiskFreeSpaceExW("C:\\", None, ctypes.byref(total), ctypes.byref(free))
print(f"Free: {free.value/(1024**3):.1f} GB")
```
