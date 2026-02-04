---
name: opencode-controller
description: "Control OpenCode programmatically via its HTTP Server API. Use when you need to run coding tasks through OpenCode headlessly, manage multiple OpenCode sessions, or integrate OpenCode into automated workflows. Supports automatic server startup, session management, async task execution, and result retrieval."
---

# OpenCode Controller

Control OpenCode programmatically via its HTTP Server API.

## What This Skill Does

This skill allows you to:
- Start and manage OpenCode HTTP server automatically
- Create and manage OpenCode sessions
- Send coding tasks to OpenCode
- Retrieve results asynchronously
- Monitor task progress

## ⚠️ Critical Requirements

### 1. Must Specify Agent

**Important:** When sending messages, you **must** specify the `agent` parameter. Without it, OpenCode will not process the message.

```powershell
# ❌ WRONG - Message will not be processed
Send-OpenCodeMessage -Controller $ctrl -SessionId $id -Message "List files"

# ✅ CORRECT - Use 'general' agent for most tasks
Send-OpenCodeMessage -Controller $ctrl -SessionId $id -Message "List files" -Agent "general"
```

**Available Agents:**
- `general` - General-purpose tasks (recommended for most use cases)
- `chief` - Complex coordination tasks
- `explore` - Codebase exploration
- `deputy`, `researcher`, `writer`, `editor` - Specialized sub-agents

### 2. Directory Access Restrictions

OpenCode can only access files in these directories:
- `D:\newtype-profile`
- `C:\Users\admin\Documents`
- `C:\Users\admin\Projects`

If you specify a working directory outside these paths, OpenCode will refuse file operations.

## Quick Start (PowerShell - Windows)

For Windows environments without Python:

```powershell
# Load the script (dot-source)
. .\scripts\opencode_controller.ps1

# Create controller
$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\my-project"

# Create session
$session = New-OpenCodeSession -Controller $ctrl -Title "Fix bug"

# Send task (CRITICAL: specify -Agent!)
$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message "Create a hello.txt file with greeting" `
    -Agent "general"

# Check response
$response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }

# Cleanup
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

## API Reference (PowerShell)

### OpenCodeController Object

```powershell
$ctrl = @{
    Port = 4096                    # Server port
    ServerHost = "127.0.0.1"       # Server host
    WorkingDir = "D:\newtype-profile"  # Working directory
    AutoStart = $true              # Auto-start server if not running
    BaseUrl = "http://127.0.0.1:4096"
}
```

### Functions

**`New-OpenCodeController`**
```powershell
$ctrl = New-OpenCodeController `
    -Port 4096 `
    -WorkingDir "D:\newtype-profile" `
    -AutoStart $true
```

**`New-OpenCodeSession`**
```powershell
$session = New-OpenCodeSession -Controller $ctrl -Title "Task description"
# Returns: @{ id = "ses_xxx"; title = "..."; ... }
```

**`Send-OpenCodeMessage`** ⭐ RECOMMENDED
```powershell
$response = Send-OpenCodeMessage `
    -Controller $ctrl `
    -SessionId $session.id `
    -Message "Your task here" `
    -Agent "general"              # REQUIRED!

# Extract text from response
$text = $response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
```

**`Send-OpenCodeMessageAsync`** ⚠️ Not Recommended
```powershell
# Fire-and-forget (may not trigger processing)
Send-OpenCodeMessageAsync -Controller $ctrl -SessionId $session.id -Message "Task"
```

**`Wait-OpenCodeCompletion`** ⚠️ Known Issues
```powershell
# May timeout even when task succeeds
$result = Wait-OpenCodeCompletion `
    -Controller $ctrl `
    -SessionId $session.id `
    -Timeout 60
```

**`Remove-OpenCodeSession`**
```powershell
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

## Usage Patterns

### Pattern 1: Simple Task with Result Verification

**Recommended approach** - Don't rely on `Wait-OpenCodeCompletion`, verify results directly:

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\my-project"
$session = New-OpenCodeSession -Controller $ctrl -Title "Create config"

# Send task
$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message "Create a config.json file with { name: 'test' }" `
    -Agent "general"

Write-Host "Task acknowledged: $($response.parts[0].text)"

# Wait for background processing
Start-Sleep -Seconds 5

# Verify result directly (don't trust API status)
if (Test-Path "D:\newtype-profile\my-project\config.json") {
    Write-Host "✓ Success!"
    Get-Content "D:\newtype-profile\my-project\config.json"
} else {
    Write-Host "✗ Task may have failed"
}

# Cleanup
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

### Pattern 2: Code Editing Task

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\project"
$session = New-OpenCodeSession -Controller $ctrl -Title "Refactor code"

# Multi-step task
$task = @"
Read the file at D:\newtype-profile\project\utils.py and:
1. Add docstrings to all functions
2. Add type hints
3. Save the updated file
"@

$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message $task `
    -Agent "general"

# Check assistant response
$response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
```

### Pattern 3: Batch Processing

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile"
$tasks = @(
    "Create file1.txt with content A",
    "Create file2.txt with content B",
    "Create file3.txt with content C"
)

$sessions = foreach ($task in $tasks) {
    $session = New-OpenCodeSession -Controller $ctrl -Title $task
    
    Send-OpenCodeMessage -Controller $ctrl `
        -SessionId $session.id `
        -Message $task `
        -Agent "general" | Out-Null
    
    $session.id
}

# Wait and verify
Start-Sleep -Seconds 10

foreach ($id in $sessions) {
    $session = Get-OpenCodeSession -Controller $ctrl -SessionId $id
    Write-Host "Session $($session.title): $($session.time.updated)"
    Remove-OpenCodeSession -Controller $ctrl -SessionId $id
}
```

## Known Issues & Limitations

### 1. Async Mode (`Send-OpenCodeMessageAsync`)
- **Status:** ⚠️ Not working reliably
- **Issue:** Messages sent via `prompt_async` endpoint may not trigger processing
- **Workaround:** Use synchronous `Send-OpenCodeMessage` instead

### 2. `Wait-ForCompletion` Status Detection
- **Status:** ⚠️ Unreliable
- **Issue:** May timeout even when task succeeds; session status endpoint returns empty
- **Workaround:** Verify results directly (e.g., check if file exists)

### 3. `Get-OpenCodeMessages` Returns Empty
- **Status:** ⚠️ Intermittent
- **Issue:** Sometimes returns empty array even when messages exist
- **Workaround:** Query directly via REST API if needed

### 4. Directory Restrictions
- **Status:** By design
- **Issue:** Can only access `D:\newtype-profile`, `C:\Users\admin\Documents`, `C:\Users\admin\Projects`
- **Workaround:** Use these directories or create symlinks

## Requirements

- OpenCode installed and available in PATH (`opencode --version`)
- PowerShell 5.1+ (Windows)
- Or Python 3.x with `requests` library

### Setup

**PowerShell (Windows - Recommended):**
```powershell
cd skills\opencode-controller\scripts
. .\opencode_controller.ps1
```

**Python (if available):**
```bash
cd scripts
pip install -r requirements.txt
python -c "from opencode_controller import OpenCodeController; print('OK')"
```

## Working Directory

Default working directory is `D:\newtype-profile`.

**Important:** OpenCode can only access files in allowed directories. The server will start in your specified directory, but file operations are restricted to:
- `D:\newtype-profile`
- `C:\Users\admin\Documents`
- `C:\Users\admin\Projects`

## Security Notes

- Server runs on localhost by default (127.0.0.1)
- No authentication in default setup (suitable for local use)
- All file operations restricted to allowed directories

## Troubleshooting

**"Server failed to start"**
```powershell
# Check OpenCode installation
opencode --version

# Check port availability
Get-NetTCPConnection -LocalPort 4096

# Check if process is running
Get-Process -Name "opencode","node"
```

**"Message not processed / No assistant response"**
- ✅ Make sure you specified `-Agent "general"`
- ✅ Check that working directory is in allowed list
- ✅ Try a simpler task first

**"Cannot access directory"**
- Use only allowed directories: `D:\newtype-profile`, `C:\Users\admin\Documents`, `C:\Users\admin\Projects`

**"Timeout waiting for completion"**
- This is a known issue with status detection
- Verify results directly instead of relying on `Wait-OpenCodeCompletion`

## Script Location

- PowerShell Controller: `scripts/opencode_controller.ps1`
- Python Controller: `scripts/opencode_controller.py`
- Requirements: `scripts/requirements.txt`

## Changelog

### 2026-02-04
- Fixed `$Host` variable conflict → `$ServerHost`
- Fixed `Start-Process` npm script issue → use `cmd /c`
- Discovered critical requirement: must specify `-Agent` parameter
- Documented directory access restrictions
- Added known issues section
