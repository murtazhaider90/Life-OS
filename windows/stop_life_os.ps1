$ErrorActionPreference = "SilentlyContinue"

$PidFile = Join-Path $env:LOCALAPPDATA "LifeOS\server.pid"
if (-not (Test-Path $PidFile)) {
    Write-Host "No Life OS background server PID was recorded."
    exit 0
}

$ServerPid = [int](Get-Content $PidFile)
$processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $ServerPid"
if ($processInfo -and $processInfo.CommandLine -match "uvicorn" -and $processInfo.CommandLine -match "app.main:app") {
    Stop-Process -Id $ServerPid -Force
    Write-Host "Life OS background server stopped."
} else {
    Write-Host "The recorded PID no longer belongs to the Life OS server; nothing was stopped."
}
Remove-Item $PidFile -Force
