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

## Quick Start

```python
from opencode_controller import OpenCodeController

# Initialize (auto-starts server if needed)
ctrl = OpenCodeController(port=4096, working_dir="D:\mojing")

# Create a session
session = ctrl.create_session(title="Fix bug in auth module")

# Send a task
ctrl.send_message(session["id"], "Fix the login bug in auth.ts where JWT tokens aren't validated properly")

# Wait for completion and get result
result = ctrl.wait_for_completion(session["id"], timeout=300)
print(result)
```

## Requirements

- OpenCode installed and available in PATH
- Python 3.x with `requests` library (or PowerShell 5.1+)

### Setup

**Option 1: Python**
```bash
cd scripts
pip install -r requirements.txt
python -c "from opencode_controller import OpenCodeController; print('OK')"
```

**Option 2: PowerShell (Windows)**
Use the PowerShell module if Python is not available:
```powershell
Import-Module .\scripts\opencode_controller.ps1
```

## API Reference

### OpenCodeController Class

#### Initialization
```python
ctrl = OpenCodeController(
    port=4096,                    # Server port
    host="127.0.0.1",            # Server host
    working_dir="D:\mojing",     # Default working directory
    auto_start=True              # Auto-start server if not running
)
```

#### Methods

**`is_server_running()`** → bool
Check if OpenCode server is running.

**`start_server()`** → bool
Start the OpenCode server. Returns True if successful.

**`create_session(title=None, parent_id=None)`** → dict
Create a new session. Returns session info with `id`.

**`send_message(session_id, message, agent=None, model=None)`** → dict
Send a message to a session. Returns message info.

**`send_async(session_id, message)`** → None
Send a message asynchronously (fire and forget).

**`get_messages(session_id, limit=50)`** → list
Get messages from a session.

**`get_session_status(session_id)`** → dict
Get session status (idle, running, error, etc.).

**`wait_for_completion(session_id, timeout=300, poll_interval=2)`** → str
Wait for session to complete and return final output.

**`list_sessions()`** → list
List all active sessions.

**`delete_session(session_id)`** → bool
Delete a session.

**`abort_session(session_id)`** → bool
Abort a running session.

## Usage Patterns

### Pattern 1: Simple Fire-and-Forget
```python
ctrl = OpenCodeController()
session = ctrl.create_session("Quick fix")
ctrl.send_async(session["id"], "Fix the typo in README.md")
# Continue with other work...
```

### Pattern 2: Wait for Result
```python
ctrl = OpenCodeController(working_dir="D:\mojing\my-project")
session = ctrl.create_session("Refactor utils")
ctrl.send_message(session["id"], "Refactor utils.ts to use async/await")
result = ctrl.wait_for_completion(session["id"], timeout=600)
```

### Pattern 3: Batch Multiple Tasks
```python
ctrl = OpenCodeController()
tasks = [
    "Add input validation to login form",
    "Write unit tests for auth module",
    "Update API documentation"
]
sessions = []
for task in tasks:
    session = ctrl.create_session(task[:30])
    ctrl.send_async(session["id"], task)
    sessions.append(session["id"])

# Check all statuses
for sid in sessions:
    status = ctrl.get_session_status(sid)
    print(f"{sid}: {status['status']}")
```

### Pattern 4: Interactive Monitoring
```python
ctrl = OpenCodeController()
session = ctrl.create_session("Build feature")
ctrl.send_message(session["id"], "Implement user profile page")

# Poll for updates
import time
while True:
    status = ctrl.get_session_status(session["id"])
    messages = ctrl.get_messages(session["id"], limit=5)
    
    print(f"Status: {status['status']}")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content'][:100]}...")
    
    if status['status'] == 'idle':
        break
    time.sleep(3)
```

## Error Handling

The controller handles common errors:
- Server not running → Auto-start or raise error
- Connection timeout → Retry with backoff
- Session not found → Clear error message
- API errors → Raise OpenCodeAPIError with details

## Working Directory

Default working directory is `D:\mojing`. OpenCode will operate in this directory unless specified otherwise in `create_session()`.

## Security Notes

- Server runs on localhost by default (127.0.0.1)
- No authentication in default setup (suitable for local use)
- All file operations happen within the working directory

## Troubleshooting

**"Server failed to start"**
- Check if OpenCode is installed: `opencode --version`
- Check if port 4096 is available
- Check OpenCode logs in terminal

**"Session timeout"**
- Increase timeout parameter
- Check if OpenCode is processing (may be slow)
- Verify working directory exists

**"Connection refused"**
- Server may have crashed
- Controller will auto-restart if `auto_start=True`

---

## PowerShell Usage (Windows)

For Windows environments without Python:

```powershell
# Import the module
Import-Module .\scripts\opencode_controller.ps1

# Create controller
$ctrl = New-OpenCodeController -WorkingDir "D:\mojing"

# Create session
$session = New-OpenCodeSession -Controller $ctrl -Title "Fix bug"

# Send task
Send-OpenCodeMessageAsync -Controller $ctrl -SessionId $session.id `
    -Message "Fix the auth bug in auth.ts"

# Wait for result
$result = Wait-OpenCodeCompletion -Controller $ctrl -SessionId $session.id -Timeout 300
Write-Host $result

# Cleanup
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

### PowerShell Quick Task

```powershell
# One-liner quick task
$ctrl = New-OpenCodeController
$session = New-OpenCodeSession -Controller $ctrl -Title "Quick fix"
Send-OpenCodeMessageAsync -Controller $ctrl -SessionId $session.id -Message "List files"
Wait-OpenCodeCompletion -Controller $ctrl -SessionId $session.id
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

## Script Location

- Controller script: `scripts/opencode_controller.py`
- Example usage: `scripts/example.py`
