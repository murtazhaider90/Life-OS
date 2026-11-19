$ErrorActionPreference = "SilentlyContinue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$StateDir = Join-Path $env:LOCALAPPDATA "LifeOS"
$ServerPidFile = Join-Path $StateDir "server.pid"
$SidecarPidFile = Join-Path $StateDir "sidecar.pid"
$EscapedRepo = [regex]::Escape($RepoRoot)

function Stop-RecordedProcess([string]$PidFile, [string]$ExpectedPattern, [string]$Label) {
    if (-not (Test-Path $PidFile)) {
        return $false
    }

    try {
        $RecordedPid = [int](Get-Content $PidFile)
    } catch {
        Remove-Item $PidFile -Force
        return $false
    }

    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $RecordedPid"
    if ($processInfo -and $processInfo.CommandLine -match $ExpectedPattern) {
        Stop-Process -Id $RecordedPid -Force
        Write-Host "$Label stopped."
        Remove-Item $PidFile -Force
        return $true
    }

    Write-Host "Recorded PID no longer belongs to $Label."
    Remove-Item $PidFile -Force
    return $false
}

$sidecarStopped = Stop-RecordedProcess $SidecarPidFile "desktop\.windows_sidecar" "Life OS sidecar"
if (-not $sidecarStopped) {
    $rogueSidecars = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and
        $_.CommandLine -match "desktop\.windows_sidecar" -and
        $_.CommandLine -match $EscapedRepo
    }
    foreach ($proc in $rogueSidecars) {
        Stop-Process -Id $proc.ProcessId -Force
        Write-Host "Untracked Life OS sidecar stopped."
    }
}

$serverStopped = Stop-RecordedProcess $ServerPidFile "uvicorn.*app\.main:app" "Life OS server"
if (-not $serverStopped) {
    $rogueServers = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and
        $_.CommandLine -match "uvicorn" -and
        $_.CommandLine -match "app\.main:app" -and
        $_.CommandLine -match $EscapedRepo
    }
    foreach ($proc in $rogueServers) {
        Stop-Process -Id $proc.ProcessId -Force
        Write-Host "Untracked Life OS server stopped."
    }
}
