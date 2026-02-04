#requires -Version 5.1

<#
.SYNOPSIS
    OpenCode Controller - PowerShell Module
    
.DESCRIPTION
    Control OpenCode programmatically via its HTTP Server API.
    PowerShell version for Windows environments without Python.
    
.EXAMPLE
    Import-Module .\opencode_controller.ps1
    $ctrl = New-OpenCodeController -WorkingDir "D:\mojing"
    $session = New-OpenCodeSession -Controller $ctrl -Title "Fix bug"
    Send-OpenCodeMessage -Controller $ctrl -SessionId $session.id -Message "Fix the auth bug"
#>

# Default configuration
$script:DefaultPort = 4096
$script:DefaultHost = "127.0.0.1"
$script:DefaultWorkingDir = "D:\mojing"

function New-OpenCodeController {
    <#
    .SYNOPSIS
        Create a new OpenCode controller instance.
    #>
    param(
        [int]$Port = $script:DefaultPort,
        [string]$Host = $script:DefaultHost,
        [string]$WorkingDir = $script:DefaultWorkingDir,
        [bool]$AutoStart = $true,
        [int]$ServerTimeout = 30
    )
    
    # Ensure working directory exists
    if (-not (Test-Path $WorkingDir)) {
        New-Item -ItemType Directory -Path $WorkingDir -Force | Out-Null
    }
    
    $controller = @{
        Port = $Port
        Host = $Host
        WorkingDir = $WorkingDir
        AutoStart = $AutoStart
        ServerTimeout = $ServerTimeout
        BaseUrl = "http://${Host}:${Port}"
        ServerProcess = $null
    }
    
    # Auto-start server if needed
    if ($AutoStart -and -not (Test-OpenCodeServer -Controller $controller)) {
        Start-OpenCodeServer -Controller $controller
    }
    
    return $controller
}

function Test-OpenCodeServer {
    <#
    .SYNOPSIS
        Check if OpenCode server is running.
    #>
    param([hashtable]$Controller)
    
    try {
        $url = "$($Controller.BaseUrl)/global/health"
        $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 2 -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Start-OpenCodeServer {
    <#
    .SYNOPSIS
        Start the OpenCode HTTP server.
    #>
    param([hashtable]$Controller)
    
    if (Test-OpenCodeServer -Controller $Controller) {
        Write-Host "OpenCode server is already running"
        return $true
    }
    
    Write-Host "Starting OpenCode server on $($Controller.Host):$($Controller.Port)..."
    
    try {
        # Check if opencode is available
        $null = Get-Command opencode -ErrorAction Stop
        
        # Start server process
        $process = Start-Process -FilePath "opencode" `
            -ArgumentList "serve", "--port", $Controller.Port, "--hostname", $Controller.Host `
            -WorkingDirectory $Controller.WorkingDir `
            -WindowStyle Hidden `
            -PassThru
        
        $Controller.ServerProcess = $process
        
        # Wait for server to be ready
        $startTime = Get-Date
        $timeout = $Controller.ServerTimeout
        
        while (((Get-Date) - $startTime).TotalSeconds -lt $timeout) {
            if (Test-OpenCodeServer -Controller $Controller) {
                Write-Host "✓ OpenCode server started at $($Controller.BaseUrl)" -ForegroundColor Green
                return $true
            }
            Start-Sleep -Milliseconds 500
        }
        
        throw "Server failed to respond within timeout period"
    }
    catch [System.Management.Automation.CommandNotFoundException] {
        throw "OpenCode not found. Please install: npm install -g opencode-ai"
    }
    catch {
        throw "Failed to start server: $_"
    }
}

function Stop-OpenCodeServer {
    <#
    .SYNOPSIS
        Stop the OpenCode server if we started it.
    #>
    param([hashtable]$Controller)
    
    if ($Controller.ServerProcess -and -not $Controller.ServerProcess.HasExited) {
        Stop-Process -Id $Controller.ServerProcess.Id -Force
        return $true
    }
    return $false
}

function Invoke-OpenCodeApi {
    <#
    .SYNOPSIS
        Make HTTP request to OpenCode API.
    #>
    param(
        [hashtable]$Controller,
        [string]$Method = "GET",
        [string]$Path,
        [hashtable]$Body = $null,
        [int]$TimeoutSec = 30
    )
    
    $url = "$($Controller.BaseUrl)/$($Path.TrimStart('/'))"
    
    try {
        $params = @{
            Uri = $url
            Method = $Method
            TimeoutSec = $TimeoutSec
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.ContentType = "application/json"
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        return $response
    }
    catch [System.Net.WebException] {
        if ($Controller.AutoStart -and -not (Test-OpenCodeServer -Controller $Controller)) {
            Start-OpenCodeServer -Controller $Controller
            # Retry once
            return Invoke-OpenCodeApi @PSBoundParameters
        }
        throw "API request failed: $_"
    }
}

function New-OpenCodeSession {
    <#
    .SYNOPSIS
        Create a new OpenCode session.
    #>
    param(
        [hashtable]$Controller,
        [string]$Title = $null,
        [string]$ParentId = $null
    )
    
    $body = @{}
    if ($Title) { $body.title = $Title }
    if ($ParentId) { $body.parentID = $ParentId }
    
    return Invoke-OpenCodeApi -Controller $Controller -Method "POST" -Path "/session" -Body $body
}

function Get-OpenCodeSession {
    <#
    .SYNOPSIS
        Get session details or list all sessions.
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId = $null
    )
    
    if ($SessionId) {
        return Invoke-OpenCodeApi -Controller $Controller -Method "GET" -Path "/session/$SessionId"
    }
    else {
        return Invoke-OpenCodeApi -Controller $Controller -Method "GET" -Path "/session"
    }
}

function Remove-OpenCodeSession {
    <#
    .SYNOPSIS
        Delete a session.
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId
    )
    
    Invoke-OpenCodeApi -Controller $Controller -Method "DELETE" -Path "/session/$SessionId"
    return $true
}

function Get-OpenCodeSessionStatus {
    <#
    .SYNOPSIS
        Get session status.
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId
    )
    
    $status = Invoke-OpenCodeApi -Controller $Controller -Method "GET" -Path "/session/status"
    return $status.$SessionId
}

function Send-OpenCodeMessage {
    <#
    .SYNOPSIS
        Send a message to a session.
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId,
        [string]$Message,
        [string]$Agent = $null,
        [string]$Model = $null,
        [switch]$NoReply
    )
    
    $body = @{
        parts = @(@{ type = "text"; text = $Message })
    }
    
    if ($Agent) { $body.agent = $Agent }
    if ($Model) { $body.model = $Model }
    if ($NoReply) { $body.noReply = $true }
    
    return Invoke-OpenCodeApi -Controller $Controller -Method "POST" `
        -Path "/session/$SessionId/message" -Body $body -TimeoutSec 120
}

function Send-OpenCodeMessageAsync {
    <#
    .SYNOPSIS
        Send a message asynchronously (fire and forget).
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId,
        [string]$Message
    )
    
    $body = @{
        parts = @(@{ type = "text"; text = $Message })
    }
    
    try {
        Invoke-RestMethod -Uri "$($Controller.BaseUrl)/session/$SessionId/prompt_async" `
            -Method POST -Body ($body | ConvertTo-Json) -ContentType "application/json" `
            -TimeoutSec 5 | Out-Null
    }
    catch {
        # Async calls may timeout, that's expected
    }
}

function Get-OpenCodeMessages {
    <#
    .SYNOPSIS
        Get messages from a session.
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId,
        [int]$Limit = 50
    )
    
    return Invoke-OpenCodeApi -Controller $Controller -Method "GET" `
        -Path "/session/$SessionId/message" -Body @{ limit = $Limit }
}

function Wait-OpenCodeCompletion {
    <#
    .SYNOPSIS
        Wait for session to complete and return result.
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId,
        [int]$Timeout = 300,
        [int]$PollInterval = 2
    )
    
    $startTime = Get-Date
    
    while (((Get-Date) - $startTime).TotalSeconds -lt $Timeout) {
        $status = Get-OpenCodeSessionStatus -Controller $Controller -SessionId $SessionId
        
        if ($status.status -eq "idle") {
            # Get last assistant message
            $messages = Get-OpenCodeMessages -Controller $Controller -SessionId $SessionId -Limit 10
            for ($i = $messages.Count - 1; $i -ge 0; $i--) {
                if ($messages[$i].role -eq "assistant") {
                    $texts = $messages[$i].parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
                    return $texts -join "\n"
                }
            }
            return ""
        }
        
        Start-Sleep -Seconds $PollInterval
    }
    
    throw "Session did not complete within $Timeout seconds"
}

function Get-OpenCodeDiff {
    <#
    .SYNOPSIS
        Get file diff for a session.
    #>
    param(
        [hashtable]$Controller,
        [string]$SessionId,
        [string]$MessageId = $null
    )
    
    $path = "/session/$SessionId/diff"
    if ($MessageId) {
        $path += "?messageID=$MessageId"
    }
    
    return Invoke-OpenCodeApi -Controller $Controller -Method "GET" -Path $path
}

# Export functions
Export-ModuleMember -Function @(
    "New-OpenCodeController",
    "Test-OpenCodeServer",
    "Start-OpenCodeServer",
    "Stop-OpenCodeServer",
    "New-OpenCodeSession",
    "Get-OpenCodeSession",
    "Remove-OpenCodeSession",
    "Get-OpenCodeSessionStatus",
    "Send-OpenCodeMessage",
    "Send-OpenCodeMessageAsync",
    "Get-OpenCodeMessages",
    "Wait-OpenCodeCompletion",
    "Get-OpenCodeDiff"
)
