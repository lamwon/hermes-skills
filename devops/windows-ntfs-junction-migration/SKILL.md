---
name: windows-ntfs-junction-migration
description: Move app data directories from C drive to another drive using NTFS directory junctions, freeing C drive space without breaking hardcoded app paths.
---

# Windows NTFS Junction Data Migration

## When to Use

An app stores its data in a hardcoded path under `%USERPROFILE%` or `%PROGRAMDATA%` (e.g., `C:\Users\<user>\.appname\`) and:
- There's no config option to change the data directory
- You want to free C drive space by moving the data to another drive
- The app must continue working transparently with no config changes

## C Drive Space Analysis Methodology

### Total Space Check
```powershell
Get-PSDrive C | Select-Object Used, Free | Format-List
```

### Tier 1: Map Top-Level Directories
```powershell
$targets = @(
    "$env:LOCALAPPDATA", "$env:APPDATA", "$env:PROGRAMDATA",
    "$env:ProgramFiles", "${env:ProgramFiles(x86)}",
    "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Documents", "$env:USERPROFILE\Downloads"
)
foreach ($t in $targets) {
    if (Test-Path $t) {
        try {
            $size = (Get-ChildItem $t -Recurse -File -ErrorAction SilentlyContinue |
                Measure-Object -Property Length -Sum).Sum
            Write-Host ("{0,-45} {1,8:N0} MB" -f $t, [math]::Round($size/1MB, 0))
        } catch { }
    }
}
```
This reveals which areas (AppData\Local, AppData\Roaming, ProgramData, Program Files) are the biggest.

### Tier 2: Drill Down into Large Directories
```powershell
# For AppData\Local
Get-ChildItem "$env:LOCALAPPDATA" -Directory | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    if ($size -gt 100MB) {
        Write-Host ("{0,-45} {1,8:N0} MB" -f $_.Name, [math]::Round($size/1MB, 0))
    }
}

# Same for other large directories
Get-ChildItem "$env:APPDATA" -Directory | ForEach-Object { ... }
Get-ChildItem "$env:PROGRAMDATA" -Directory | ForEach-Object { ... }
```

### Tier 3: Quick File Type Breakdown (for cache directories)
```powershell
# See what types of files are taking space
Get-ChildItem "C:\Path\To\Dir" -Recurse -File |
    Group-Object Extension |
    Sort-Object Count -Desc |
    Select-Object Count, Name, @{N='Size(MB)';E={[math]::Round(($_.Group |
        Measure-Object -Property Length -Sum).Sum/1MB, 1)}}
```

### Common Space Hogs to Check

| Directory | Typical Size | Migration Viability |
|-----------|-------------|-------------------|
| `%LOCALAPPDATA%\Temp` | 100MB-2GB | Safe to delete entirely |
| `%LOCALAPPDATA%\npm-cache` | 100-500MB | `npm cache clean --force` |
| `%LOCALAPPDATA%\Microsoft\Edge` | 500MB-1GB | Junction from `%LOCALAPPDATA%\Microsoft` |
| `%LOCALAPPDATA%\Programs` | 1-3GB | Usually Python/VSCode/Node - check before moving |
| `%APPDATA%\kingsoft` (WPS) | 2-5GB | **Junction** — but kill wpscloudsvr.exe first |
| `%APPDATA%\Tencent\xwechat` | 500MB-1.5GB | **Junction** — kill WeChat first |
| `%APPDATA%\Tencent\QQ` | 200-500MB | Junction or clean |
| `%PROGRAMDATA%\Anaconda3` | 2-5GB | **Junction** — requires admin (see ProgramData section) |
| `%PROGRAMDATA%\Adobe\CameraRaw` | ~900MB | Not worth migrating (small) |
| `%PROGRAMDATA%\Autodesk` | 1-2GB | Junction — requires admin |

### Quick Cleanup Candidates (no migration needed)

These can be safely deleted without any migration:
- `%LOCALAPPDATA%\Temp\*` — OS temp files
- `%WINDIR%\Temp\*` — System temp files
- `%LOCALAPPDATA%\npm-cache` — Node.js package cache
- `$Recycle.Bin` — Recycle bin (use `cleanmgr` or `rd /S`)

## Migration Priority Assessment

Before migrating, identify the biggest space consumers:

```powershell
# Quick overview of large directories (100MB+)
$targets = @(
    "$env:LOCALAPPDATA",
    "$env:APPDATA",
    "$env:PROGRAMDATA",
    "$env:ProgramFiles",
    "${env:ProgramFiles(x86)}",
    "$env:USERPROFILE\Desktop",
    "$env:USERPROFILE\Documents",
    "$env:USERPROFILE\Downloads"
)
foreach ($t in $targets) {
    if (Test-Path $t) {
        $size = (Get-ChildItem $t -Recurse -File -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
        Write-Host ("{0,-45} {1,8:N0} MB" -f $t, [math]::Round($size/1MB, 0))
    }
}

# Drill into a specific directory to see sub-folder breakdown
Get-ChildItem "$env:LOCALAPPDATA" -Directory | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    if ($size -gt 100MB) {
        Write-Host ("{0,-45} {1,8:N0} MB" -f $_.Name, [math]::Round($size/1MB, 0))
    }
}
```

### Migration Priority Assessment

| Category | Examples | Size Range | Migration Method | Notes |
|----------|----------|-----------|-----------------|-------|
| User cache | npm-cache, Temp, browser cache | 100MB-2GB | `clean` (just delete) | Safe to clean anytime |
| User app data | WorkBuddy, Claude Code, WPS, WeChat | 100MB-5GB | `junction` from `%APPDATA%` or `%LOCALAPPDATA%` | No admin needed for junction |
| Shared app data | Adobe CameraRaw, Anaconda3 | 0.5-4GB | `junction` from `%PROGRAMDATA%` | **Requires admin** for rmdir + mklink |
| Installed programs | Microsoft Office, games | 1-20GB | uninstall + reinstall to D | Not junction-safe |
| System | Windows, WinSxS, pagefile | 10-40GB | Do NOT touch | Use `cleanmgr` built-in tool |

## Strategy

Use **NTFS Directory Junction** (`mklink /J`): the original C drive path becomes a reparse point pointing to the new location on D drive. The app reads/writes transparently — Windows handles all redirection at the filesystem level.

## Step-by-Step Migration

### Phase 1: Investigate

```bash
# Find the app's data directory size
du -sh ~/.appname/

# Check if a config option exists (sometimes it's hidden)
cat ~/.appname/config.json 2>/dev/null | grep -i path
cat ~/.appname/settings.json 2>/dev/null | grep -i path
```

### Phase 2: Stop all related processes

**⚠️ Watch for background process resurrection**: Some apps (WPS, WeChat) have services like `wpscloudsvr.exe` that recreate data directories immediately after deletion. Kill them AND create the junction in one rapid sequence using `rd /S /Q` (cmd) not `Remove-Item` (PowerShell).

```bash
# Kill the main app
taskkill //F //IM "AppName.exe"

# Kill any child processes using the app's files
tasklist //FI "IMAGENAME eq python*" //FO LIST

# WorkBuddy has its own embedded Python that locks .pyd/.dll files.
# Find its PID via the EXE path, not just the name:
powershell -Command "Get-Process python* | Select-Object Id, Path | Format-Table -AutoSize"
taskkill //F //PID <PID>

# Kill proxy/helper processes
taskkill //F //IM "cc-switch.exe"
```

### Phase 3: Copy data with robocopy

**IMPORTANT**: Use `/COPY:DAT` NOT `/COPYALL`. The `/COPYALL` flag requires the `Manage Auditing` user right and will fail with `ERROR: You do not have the Manage Auditing user right`.

```powershell
# Create target directory
mkdir D:\AppData\.appname

# Copy files preserving data + attributes + timestamps only (no security/audit)
robocopy "%USERPROFILE%\.appname" "D:\AppData\.appname" /E /COPY:DAT /DCOPY:T /R:1 /W:2
```

Verify the copy:

```powershell
$srcFiles = (Get-ChildItem "%USERPROFILE%\.appname" -Recurse -File | Measure-Object).Count
$dstFiles = (Get-ChildItem "D:\AppData\.appname" -Recurse -File | Measure-Object).Count
$srcSize = (Get-ChildItem "%USERPROFILE%\.appname" -Recurse -File |
    Measure-Object -Property Length -Sum).Sum
$dstSize = (Get-ChildItem "D:\AppData\.appname" -Recurse -File |
    Measure-Object -Property Length -Sum).Sum
Write-Host "Source: $srcFiles files, $([math]::Round($srcSize/1MB,0)) MB"
Write-Host "Dest:   $dstFiles files, $([math]::Round($dstSize/1MB,0)) MB"
if ($srcFiles -ne $dstFiles) { Write-Host "MISMATCH!" -ForegroundColor Red }
```

### Phase 4: Remove original and create junction

If some files are locked (e.g., Python .pyd/.dll files), you may get permission errors. Find and kill the locking process first (see Phase 2), then:

```powershell
# Delete the original directory (use cmd /c rmdir not Remove-Item for large trees)
cmd /c "rmdir /S /Q \"%USERPROFILE%\.appname\""

# Create the junction (does NOT require admin on Win10/11 for directory junctions in %USERPROFILE%)
cmd /c "mklink /J \"%USERPROFILE%\.appname\" \"D:\AppData\.appname\""
```

**For `%PROGRAMDATA%` paths**: The current user typically has only `ReadAndExecute` + `Write` permissions, not `Modify`/`Delete`. You MUST run as administrator:

```powershell
# Option A: Run a batch script as admin
Start-Process cmd -Verb RunAs -ArgumentList '/c rmdir /S /Q "C:\ProgramData\AppName" && mklink /J "C:\ProgramData\AppName" "D:\ProgramData\AppName"'

# Option B: If rmdir fails even as admin due to locked files, use takeown + icacls first:
takeown /F "C:\ProgramData\AppName" /R /D Y
icacls "C:\ProgramData\AppName" /grant "Users:(OI)(CI)F" /T /Q
rmdir /S /Q "C:\ProgramData\AppName"
mklink /J "C:\ProgramData\AppName" "D:\ProgramData\AppName"
```

Junctions (`mklink /J`) do NOT require administrator privileges on modern Windows in user profile paths — only symbolic links (`mklink /D`) need admin. But for `ProgramData`, the DELETE operation on the original files requires admin, not the junction creation itself.

### The "Empty Subdirectory" Gotcha

When an admin process deletes files (via `takeown + icacls + rmdir`), **files are removed but empty subdirectories may persist**. If a background service is still running, it may instantly recreate empty dirs as part of its heartbeat.

**Symptoms**:
- Files = 0, but empty subdirectories still exist
- `Get-Item` shows `LinkType: ` (empty) not `LinkType: Junction`
- `mklink /J` fails with "Cannot create a file when that file already exists"

**Fix**: Kill background processes, then use `cmd /c "rd /S /Q"` (not `Remove-Item -Recurse`), then immediately create the junction.

### Phase 5: Verify

```powershell
$item = Get-Item "%USERPROFILE%\.appname"
Write-Host "LinkType: $($item.LinkType)"   # Should say "Junction"
Write-Host "Target: $($item.Target)"       # Should show D drive path
```

Also do a file write test:

```bash
touch ~/.appname/.migration_test
ls D:/AppData/.appname/.migration_test
rm ~/.appname/.migration_test
```

### Phase 6: Restart services

```powershell
# Restart any proxy/helper processes
start "" "%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe"
```

## Bulk Migration: Batch Script Pattern

For moving multiple directories at once, write a batch script and run it as admin:

```batch
@echo off
chcp 65001 >nul
title C盘空间迁移
color 0B

REM === MIGRATE EACH APP ===
set "SRC=C:\ProgramData\Anaconda3"
set "DST=D:\ProgramData\Anaconda3"

if exist "%SRC%" (
    if not exist "%DST%" robocopy "%SRC%" "%DST%" /E /COPY:DAT /R:1 /W:2 /NFL /NDL
    takeown /F "%SRC%" /R /D Y >nul 2>&1
    icacls "%SRC%" /grant "Users:(OI)(CI)F" /T /Q >nul 2>&1
    rmdir /S /Q "%SRC%" >nul 2>&1
    if not exist "%SRC%" (
        mklink /J "%SRC%" "%DST%" >nul
        echo [OK] %SRC% migrated
    ) else (
        echo [FAIL] Could not delete %SRC% - process may have it locked
    )
)
```

Launch it with admin:

```powershell
Start-Process cmd -Verb RunAs -ArgumentList '/c D:\migrate_script.bat & pause'
```

This triggers a UAC prompt. The user must click "Yes" for it to proceed. The script runs asynchronously — you cannot wait for its completion in the calling shell. Wait ~5-10 seconds, then verify:
```powershell
$item = Get-Item "C:\Target\Path"
Write-Host $item.LinkType  # Should say "Junction" if admin script succeeded
```

## PowerShell Remove-Item vs cmd rmdir — practical difference

After killing the locking process, **use `cmd /c "rmdir /S /Q"` from PowerShell rather than `Remove-Item -Recurse -Force`**. The `rmdir /S /Q` approach is more robust for large directory trees with deep nesting of files that may have had their handles partially released. If `Remove-Item` fails with "directory is not empty" after killing the lock holder, `rd /S /Q` often succeeds where PowerShell gives up.

## Dealing with Background Process Resurrection

Some apps (especially WPS/Kingsoft, WeChat) have background services that **recreate their data directories immediately after deletion**. This prevents junction creation with: `Cannot create a file when that file already exists.`

**Common offenders and their processes:**

| App | Background Process | Detection |
|-----|-------------------|-----------|
| WPS Office | `wpscloudsvr.exe`, `wps.exe` | `powershell "Get-Process *wps*, *kingsoft* \| Select-Object Id, ProcessName"` |
| WeChat | `WeChat.exe`, `xwechat.exe` | `powershell "Get-Process *wechat*, *xwechat* \| Select-Object Id, ProcessName"` |

**Solution**: Kill the background process, then **immediately** delete and create the junction before the process restarts:

```powershell
taskkill //F //IM "wpscloudsvr.exe" 2>$null
taskkill //F //IM "wps.exe" 2>$null
Start-Sleep -Seconds 1

# Delete original (files already gone, but empty dirs remain)
cmd /c "rd /S /Q \"%APPDATA%\\kingsoft\""

# Create junction immediately
cmd /c "mklink /J \"%APPDATA%\\kingsoft\" \"D:\\AppData\\kingsoft\""
```

The `rd /S /Q` approach from cmd is more reliable than `Remove-Item -Recurse` for this pattern, as it handles the empty-directory-resurrection edge case better.

## The "Empty Subdirectory" Gotcha

When an admin process deletes files (e.g., via `takeown + icacls + rmdir`), **files are removed but empty subdirectories may persist**. If the app's background service is still running, it may instantly recreate empty subdirectories as part of its heartbeat/watchdog mechanism.

**Symptoms**:
- `rmdir /S /Q` reports "Access is denied" for some files
- After the admin script completes, the directory still exists but has 0 files
- `Get-Item` shows `LinkType: ` (empty) instead of `LinkType: Junction`
- `mklink /J` fails with "Cannot create a file when that file already exists"

**Fix**: Kill all related processes, then `rd /S /Q` from cmd (not Remove-Item from PowerShell), then immediately create the junction.

## Bulk Migration: Self-Contained Batch Script

For moving multiple directories at once, write a batch script. Key patterns:

### Correct robocopy flags
```batch
robocopy "%SRC%" "%DST%" /E /COPY:DAT /R:1 /W:2
```
- `/COPY:DAT` — copies Data + Attributes + Timestamps (NOT `/COPYALL` which needs admin)
- `/R:1 /W:2` — only 1 retry with 2-second wait

### Handling ProgramData paths
For `C:\ProgramData\` paths, always use these steps in order:
```batch
takeown /F "%SRC%" /R /D Y >nul 2>&1
icacls "%SRC%" /grant "Users:(OI)(CI)F" /T /Q >nul 2>&1
rmdir /S /Q "%SRC%" >nul 2>&1
if not exist "%SRC%" (
    mklink /J "%SRC%" "%DST%" >nul
)
```

### Launching with admin
```batch
powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c D:\script.bat & pause'"
```

## Dealing with Locked Files

When deleting the original directory, you may encounter errors like:

```
Access to the path 'libcrypto-3-x64.dll' is denied.
Access to the path 'python.exe' is denied.
```

This means a process still has those files open. Common culprits:

| File Pattern | Likely Owner | Find Command |
|-------------|-------------|--------------|
| `.pyd`, `.dll`, `python.exe` | Embedded Python process | `powershell -Command "Get-Process python* \| Select-Object Id, Path \| Format-Table -AutoSize"` — look for the one under `C:\Users\Windows\.workbuddy\binaries\python\` |
| `.exe` | The main app | `tasklist //FI "IMAGENAME eq appname.exe"` |
| `.db`, `.db-wal`, `.db-shm` | SQLite database process | Use `handle.exe` from Sysinternals |

⚠️ `takeown` and `icacls` will NOT help if the file is open by a process. You must kill the process holding the lock. Rebooting is the nuclear option.

### PowerShell Remove-Item vs cmd rmdir — practical difference

After killing the locking process, **use `cmd /c "rmdir /S /Q"` from PowerShell rather than `Remove-Item -Recurse -Force`**. The `rmdir /S /Q` approach is more robust for large directory trees with deep nesting of files that may have had their handles partially released. If `Remove-Item` fails with "directory is not empty" after killing the lock holder, `rmdir /S /Q` often succeeds where PowerShell gives up.

## Cleanup: Remove Installation Temp Dirs

After migration, you can free additional space by removing stale installer temp directories:

```bash
rm -rf ~/.appname/binaries/node/*installing*/
```

These are left over from failed or interrupted updates.

## Dealing with Background Process Resurrection

Some apps (especially WPS/Kingsoft, WeChat) have background services that **recreate their data directories immediately after deletion**. This prevents junction creation with: `Cannot create a file when that file already exists.`

**Common offenders and their processes:**

| App | Background Process | Detection |
|-----|-------------------|-----------|
| WPS Office | `wpscloudsvr.exe`, `wps.exe` | `powershell "Get-Process *wps*, *kingsoft* \| Select-Object Id, ProcessName"` |
| WeChat | `WeChat.exe`, `xwechat.exe` | `powershell "Get-Process *wechat*, *xwechat* \| Select-Object Id, ProcessName"` |

**Solution**: Kill the background process, then **immediately** delete and create the junction before the process restarts:

```powershell
taskkill //F //IM "wpscloudsvr.exe" 2>$null
taskkill //F //IM "wps.exe" 2>$null
Start-Sleep -Seconds 1

# Delete original (files already gone, but empty dirs remain)
cmd /c "rd /S /Q \"%APPDATA%\kingsoft\""

# Create junction immediately
cmd /c "mklink /J \"%APPDATA%\kingsoft\" \"D:\AppData\kingsoft\""
```

The `rd /S /Q` approach from cmd is more reliable than `Remove-Item -Recurse` for this pattern, as it handles the empty-directory-resurrection edge case better.

## The "Empty Subdirectory" Gotcha

When an admin process deletes files (e.g., via `takeown + icacls + rmdir`), **files are removed but empty subdirectories may persist**. If the app's background service is still running, it may instantly recreate empty subdirectories as part of its heartbeat/watchdog mechanism.

**Symptoms**:
- `rmdir /S /Q` reports "Access is denied" for some files
- After the admin script completes, the directory still exists but has 0 files
- `Get-Item` shows `LinkType: ` (empty) instead of `LinkType: Junction`
- `mklink /J` fails with "Cannot create a file when that file already exists"

**Fix**: Kill all related processes, then `rd /S /Q` from cmd (not Remove-Item from PowerShell), then immediately create the junction.

## Bulk Migration: Self-Contained Batch Script

For moving multiple directories at once, write a batch script. Key patterns:

### Correct robocopy flags
```batch
robocopy "%SRC%" "%DST%" /E /COPY:DAT /R:1 /W:2
```
- `/COPY:DAT` — copies Data + Attributes + Timestamps (NOT `/COPYALL` which needs admin)
- `/R:1 /W:2` — only 1 retry with 2-second wait

### Handling ProgramData paths
For `C:\ProgramData\` paths, always use these steps in order:
```batch
takeown /F "%SRC%" /R /D Y >nul 2>&1
icacls "%SRC%" /grant "Users:(OI)(CI)F" /T /Q >nul 2>&1
rmdir /S /Q "%SRC%" >nul 2>&1
if not exist "%SRC%" (
    mklink /J "%SRC%" "%DST%" >nul
)
```

### Launching with admin
```batch
powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c D:\script.bat & pause'"
```

## VS Code Migration: The Extreme Case

VS Code is the most aggressive process-resurrector you'll encounter. Expect **16+ `Code.exe` processes** running simultaneously (main window, extension hosts, debuggers, language servers, terminal sessions). It also auto-restarts killed processes within 1-3 seconds.

### Key Challenges

| Challenge | Detail |
|-----------|--------|
| Process count | 15-20+ Code.exe processes at any time |
| Resurrection speed | Killed processes restart in 1-3 seconds |
| Locked files | `.db`, `.db-wal`, `.db-shm` (SQLite), log files, extension cache |
| Recreated dirs | `%APPDATA%\Code` and `%USERPROFILE%\.vscode` are recreated instantly with minimal files |

### Strategy

**If migrating from within VS Code's integrated terminal** (as is typical):
- You CANNOT fully migrate `%APPDATA%\Code` — VS Code auto-recreates its directory immediately after deletion
- The bulk data (extensions, workspaces, settings) will copy successfully via robocopy
- Only lightweight log files (~1MB) and temp cache remain at the original path
- **Best approach**: Move most data with robocopy /MOVE, accept a few MB of logs will remain until VS Code is fully closed

**If migrating from outside VS Code** (e.g., from another terminal emulator):
1. Kill ALL Code processes aggressively:
   ```powershell
   Get-Process | Where-Object { $_.ProcessName -match "Code" } | Stop-Process -Force
   Start-Sleep -Seconds 3
   ```
2. Use robocopy with `/MOVE` to copy and delete source in one step:
   ```powershell
   robocopy "%APPDATA%\Code" "D:\Migrated\Roaming\Code" /E /MOVE /COPY:DAT /R:1 /W:1
   ```
3. If rmdir still fails (locked files), try the rename fallback:
   ```powershell
   # Rename first, then delete
   cmd /c "move `"%APPDATA%\Code`" `"%APPDATA%\_Code_old`""
   cmd /c "rmdir /s /q `"%APPDATA%\_Code_old`""
   ```
4. Create junction immediately:
   ```powershell
   cmd /c "mklink /J `"%APPDATA%\Code`" `"D:\Migrated\Roaming\Code`""
   ```

### The Rename Fallback

When `rmdir /S /Q` fails even after `takeown` + `icacls`, the rename-then-delete approach often works because renamed directories are no longer recognized by the locking process:

```powershell
cmd /c "move `"C:\path\to\locked\dir`" `"C:\path\to\locked\dir_old`""
cmd /c "rmdir /s /q `"C:\path\to\locked\dir_old`""
```

This works because:
- The lock holder still has a handle to the old path, but the directory entry is gone
- After rename, the original path is free for junction creation
- The renamed directory can be deleted at leisure (or after reboot)

### Robocopy /MOVE vs Separate Copy+Delete

Using `/MOVE` flag is strictly superior to separate `robocopy` + `Remove-Item`:

```powershell
# GOOD: unified approach
robocopy "SRC" "DST" /E /MOVE /COPY:DAT /R:1 /W:1

# WORSE: two-step approach (more failure points)
robocopy "SRC" "DST" /E /COPY:DAT /R:1 /W:1
Remove-Item "SRC" -Recurse -Force
```

`/MOVE` deletes files from source as they're successfully copied, so partial failures leave less debris.

## PowerShell Script Execution from Git Bash / Hermes Terminal

When running PowerShell commands from within Git Bash (common in Hermes Agent/Claude Code sessions), **the `$_` variable is intercepted** by the shell or Hermes sandbox, replaced with `__HERMES_FENCE_*__`, which breaks `ForEach-Object` pipeline syntax.

### Symptoms

```powershell
# This inline command FAILS from Git Bash:
Get-ChildItem $path | ForEach-Object { Write-Host $_.Name }
# $_ becomes __HERMES_FENCE_abc123__ causing parse errors
```

### Solution: Use Script Files

**Always write complex PowerShell to a `.ps1` file first, then execute it:**

```powershell
# Write the script to a file
# Use Write-Output with full variable paths
$script = @'
$d = Get-PSDrive C
$free = [math]::Round($d.Free / 1GB, 1)
Write-Output ("Free: " + $free + " GB")
'@
Set-Content -Path "$env:TEMP\script.ps1" -Value $script

# Execute via PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:TEMP\script.ps1"
```

**Alternative: Escape `$` for inline commands**

Use backslash-escaped `\$` to prevent Git Bash from consuming the dollar sign:

```bash
powershell -Command "Get-ChildItem 'C:\Path' | ForEach-Object { Write-Host (\$_.Name) }"
```

But script files are more reliable for anything beyond 1-2 lines.

### Complete Migration Script Template

Here's a battle-tested PowerShell script template for batch migrating multiple directories, with proper error handling for VS Code edge cases:

```powershell
# save as migrate.ps1, run with: powershell -ExecutionPolicy Bypass -File migrate.ps1
param(
    [string]$SourceRoot = "C:\",
    [string]$DestRoot = "D:\Hermes\Migrated"
)

function Migrate-Junction {
    param([string]$Source, [string]$Dest)
    
    # Check if already a junction
    $item = Get-Item $Source -Force -ErrorAction SilentlyContinue
    if ($item -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        Write-Output ("[SKIP] Already junction: " + $Source)
        return $true
    }
    
    $parent = Split-Path $Dest -Parent
    if (-not (Test-Path $parent)) { New-Item -Path $parent -ItemType Directory -Force | Out-Null }
    
    # Step 1: robocopy to destination
    Write-Output ("[COPY] " + $Source + " -> " + $Dest)
    robocopy $Source $Dest /E /COPY:DAT /R:1 /W:1 /NP /NJH /NJS 2>$null
    
    # Step 2: verify
    $srcCount = (Get-ChildItem $Source -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
    $dstCount = (Get-ChildItem $Dest -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Output ("  Files: src=$srcCount dst=$dstCount")
    
    # Step 3: remove source (try robocopy /MOVE cleanup first)
    robocopy $Source $Dest /E /MOVE /COPY:DAT /R:0 /W:0 /NP /NJH /NJS 2>$null
    Start-Sleep -Seconds 2
    
    # Step 4: if source still exists, use rmdir
    if (Test-Path $Source) {
        Write-Output ("  Source persists, using rmdir...")
        cmd /c "rmdir /s /q `"$Source`"" 2>$null
        Start-Sleep -Seconds 2
    }
    
    # Step 5: if source STILL exists (locked files), try rename fallback
    if (Test-Path $Source) {
        Write-Output ("  Still locked, trying rename fallback...")
        cmd /c "move `"$Source`" `"${Source}_old`"" 2>$null
        Start-Sleep -Seconds 1
    }
    
    # Step 6: create junction
    cmd /c "mklink /J `"$Source`" `"$Dest`"" 2>$null
    
    # Verify
    $item = Get-Item $Source -Force -ErrorAction SilentlyContinue
    $isJunction = $item -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
    if ($isJunction) {
        Write-Output ("[OK] " + $Source + " -> " + $item.Target)
        return $true
    } else {
        Write-Output ("[FAIL] " + $Source + " - directory still on C")
        return $false
    }
}

# === Usage Examples ===
# Migrate-Junction "C:\Users\Windows\AppData\Roaming\Code" "D:\Hermes\Migrated\Roaming\Code"
# Migrate-Junction "C:\Users\Windows\.vscode" "D:\.vscode"
# Migrate-Junction "C:\Users\Windows\AppData\Roaming\LarkShell" "D:\Hermes\Migrated\Roaming\LarkShell"
```

## Pitfalls

- **Do NOT use `/COPYALL` with robocopy** — requires `Manage Auditing` right, will fail
- **Do NOT delete the C drive directory after copying until you verify the copy is complete**
- **Do NOT use `takeown`/`icacls` for locked files** — those are access control tools, they don't unload in-memory file handles
- **Junctions survive reboots** — the C drive path reparse point persists across restarts
- **Do NOT delete/move the D drive data while the junction exists** — the junction becomes a dead link
- **Do NOT use Junction for the entire `%USERPROFILE%`** — that would break Windows severely. Only use it for specific app data directories
- **WorkBuddy-specific**: Its Python runtime (`binaries/python/versions/3.13.12/`) locks .pyd and .dll files even when the GUI is closed. Check for a background `python.exe` process using its embedded Python path, not just any `python.exe`
- **ProgramData permission asymmetry**: The user can READ files in `C:\ProgramData\` without admin, but cannot DELETE them. Always use admin elevation for ProgramData migrations
