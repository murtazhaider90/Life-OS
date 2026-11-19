$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$PythonW = Join-Path $RepoRoot ".venv\Scripts\pythonw.exe"
$StateDir = Join-Path $env:LOCALAPPDATA "LifeOS"
$PidFile = Join-Path $StateDir "server.pid"

if (-not (Test-Path $Python)) {
    Write-Host "Life OS virtual environment was not found." -ForegroundColor Red
    Write-Host "Run python -m venv .venv and python -m pip install -e .[dev] once first."
    Read-Host "Press Enter to close"
    exit 1
}

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
Set-Location $RepoRoot

$ServerRunning = $false
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
    if ($health.status -eq "ok") { $ServerRunning = $true }
} catch {}

if (-not $ServerRunning) {
    $server = Start-Process -FilePath $PythonW -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru
    Set-Content -Path $PidFile -Value $server.Id

    $deadline = (Get-Date).AddSeconds(15)
    do {
        Start-Sleep -Milliseconds 400
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
            if ($health.status -eq "ok") { $ServerRunning = $true; break }
        } catch {}
    } while ((Get-Date) -lt $deadline)
}

if (-not $ServerRunning) {
    Write-Host "Life OS server did not start. Run Uvicorn manually to see the error." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

Start-Process -FilePath $PythonW -ArgumentList "-m","desktop.windows_sidecar" -WorkingDirectory $RepoRoot

Write-Host "Life OS is running." -ForegroundColor Green
Write-Host "Ctrl + Alt + Space shows/hides the assistant."
Write-Host "Dashboard: http://127.0.0.1:8000"
Start-Sleep -Seconds 2
