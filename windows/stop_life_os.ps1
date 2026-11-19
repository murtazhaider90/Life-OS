$ErrorActionPreference = "SilentlyContinue"

$StateDir = Join-Path $env:LOCALAPPDATA "LifeOS"
$ServerPidFile = Join-Path $StateDir "server.pid"
$SidecarPidFile = Join-Path $StateDir "sidecar.pid"

function Stop-RecordedProcess([string]$PidFile, [string]$ExpectedPattern, [string]$Label) {
    if (-not (Test-Path $PidFile)) {
        Write-Host "No recorded $Label PID."
        return
    }

    $RecordedPid = [int](Get-Content $PidFile)
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $RecordedPid"
    if ($processInfo -and $processInfo.CommandLine -match $ExpectedPattern) {
        Stop-Process -Id $RecordedPid -Force
        Write-Host "$Label stopped."
    } else {
        Write-Host "Recorded PID no longer belongs to $Label; nothing was stopped."
    }
    Remove-Item $PidFile -Force
}

Stop-RecordedProcess $SidecarPidFile "desktop\.windows_sidecar" "Life OS sidecar"
Stop-RecordedProcess $ServerPidFile "uvicorn.*app\.main:app" "Life OS server"
