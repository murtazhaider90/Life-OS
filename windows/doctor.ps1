$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$StateDir = Join-Path $env:LOCALAPPDATA "LifeOS"

Write-Host ""
Write-Host "=== Life OS Windows Doctor ===" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host "Logs: $StateDir"
Write-Host ""

function Check([string]$Name, [scriptblock]$Action) {
    Write-Host -NoNewline ("{0,-34}" -f $Name)
    try {
        & $Action
        Write-Host " OK" -ForegroundColor Green
    } catch {
        Write-Host " FAIL" -ForegroundColor Red
        Write-Host ("  " + $_.Exception.Message) -ForegroundColor Yellow
    }
}

Check "Virtual environment exists" {
    if (-not (Test-Path $Python)) { throw "Missing $Python" }
}

if (Test-Path $Python) {
    Check "Python starts" {
        $v = & $Python --version 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($v -join " ") }
        Write-Host -NoNewline " ($v)"
    }

    Check "Life OS imports" {
        $out = & $Python -c "import app.main, desktop.client, desktop.windows_sidecar; print('imports ok')" 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($out -join [Environment]::NewLine) }
    }

    Check "Tkinter can open a window" {
        $out = & $Python -c "import tkinter as tk; r=tk.Tk(); r.withdraw(); r.update_idletasks(); r.destroy(); print('tk ok')" 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($out -join [Environment]::NewLine) }
    }
}

Check "Port 8000 backend health" {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3
    if ($health.status -ne "ok") { throw "Health endpoint did not return ok." }
    Write-Host -NoNewline " (v$($health.version))"
}

Check "Assistant API responds" {
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/assistant/status" -TimeoutSec 3
    if ($null -eq $status.needs_input) { throw "Unexpected assistant response." }
}

Write-Host ""
Write-Host "PowerShell policy: $(Get-ExecutionPolicy)"
Write-Host "Current branch:"
try { git -C $RepoRoot branch --show-current } catch {}

Write-Host ""
Write-Host "Recent logs:" -ForegroundColor Cyan
foreach ($name in "server.err.log","sidecar.err.log") {
    $path = Join-Path $StateDir $name
    Write-Host "--- $name ---"
    if (Test-Path $path) { Get-Content $path -Tail 30 } else { Write-Host "(no log file)" }
}

Write-Host ""
Write-Host "If anything above says FAIL, copy everything from this window and send it to me." -ForegroundColor Yellow
Read-Host "Press Enter to close"
