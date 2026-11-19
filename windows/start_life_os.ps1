$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$StateDir = Join-Path $env:LOCALAPPDATA "LifeOS"
$ServerPidFile = Join-Path $StateDir "server.pid"
$SidecarPidFile = Join-Path $StateDir "sidecar.pid"
$ServerOut = Join-Path $StateDir "server.out.log"
$ServerErr = Join-Path $StateDir "server.err.log"
$SidecarOut = Join-Path $StateDir "sidecar.out.log"
$SidecarErr = Join-Path $StateDir "sidecar.err.log"
$NL = [Environment]::NewLine

function Show-LifeOSError([string]$Title, [string]$Message) {
    [System.Windows.Forms.MessageBox]::Show($Message,$Title,[System.Windows.Forms.MessageBoxButtons]::OK,[System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
}
function Tail-OrEmpty([string]$Path) {
    if (Test-Path $Path) { return ((Get-Content $Path -Tail 25 -ErrorAction SilentlyContinue) -join $NL) }
    return ""
}
function Get-RecordedProcess([string]$PidFile) {
    if (-not (Test-Path $PidFile)) { return $null }
    try {
        $RecordedPid = [int](Get-Content $PidFile -ErrorAction Stop)
        return Get-Process -Id $RecordedPid -ErrorAction SilentlyContinue
    } catch {
        return $null
    }
}

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

if (-not (Test-Path $Python)) {
    $msg = "The virtual environment was not found at:" + $NL + $Python + $NL + $NL + "Open PowerShell in the Life-OS folder and run:" + $NL + "python -m venv .venv" + $NL + ".venv\Scripts\Activate.ps1" + $NL + 'python -m pip install -e ".[dev]"'
    Show-LifeOSError "Life OS setup incomplete" $msg
    exit 1
}

Set-Location $RepoRoot

# Import check must never reuse the live sidecar log: a running sidecar keeps that
# file handle open on Windows. Capture diagnostics in memory instead.
$importOutput = & $Python -c "import app.main, desktop.windows_sidecar, tkinter; print('imports ok')" 2>&1
if ($LASTEXITCODE -ne 0) {
    $detail = ($importOutput -join $NL)
    Show-LifeOSError "Life OS could not load" ("The desktop components could not be imported." + $NL + $NL + $detail + $NL + $NL + "Run windows\doctor.ps1 for a full check.")
    exit 1
}

$ServerRunning = $false
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
    if ($health.status -eq "ok") { $ServerRunning = $true }
} catch {}

if (-not $ServerRunning) {
    Remove-Item $ServerOut,$ServerErr -Force -ErrorAction SilentlyContinue
    try {
        $server = Start-Process -FilePath $Python -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $ServerOut -RedirectStandardError $ServerErr -PassThru
        Set-Content -Path $ServerPidFile -Value $server.Id
    } catch {
        Show-LifeOSError "Life OS server failed" ("Could not start the local server." + $NL + $NL + $_.Exception.Message + $NL + $NL + "Run windows\doctor.ps1 for details.")
        exit 1
    }

    $deadline = (Get-Date).AddSeconds(15)
    do {
        Start-Sleep -Milliseconds 400
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
            if ($health.status -eq "ok") { $ServerRunning = $true; break }
        } catch {}
        if ($server.HasExited) { break }
    } while ((Get-Date) -lt $deadline)
}

if (-not $ServerRunning) {
    $detail = Tail-OrEmpty $ServerErr
    Show-LifeOSError "Life OS server did not start" ("The backend failed to start." + $NL + $NL + $detail + $NL + $NL + "Logs are in:" + $NL + $StateDir + $NL + $NL + "Run windows\doctor.ps1 for a full check.")
    exit 1
}

$oldSidecar = Get-RecordedProcess $SidecarPidFile
if ($oldSidecar) {
    [System.Windows.Forms.MessageBox]::Show("Life OS is already running." + $NL + $NL + "Press Ctrl + Alt + Space to show the assistant.","Life OS",[System.Windows.Forms.MessageBoxButtons]::OK,[System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null
    exit 0
}

# No recorded sidecar is alive, so these log files should be safe to rotate.
Remove-Item $SidecarOut,$SidecarErr -Force -ErrorAction SilentlyContinue
try {
    $sidecar = Start-Process -FilePath $Python -ArgumentList "-m","desktop.windows_sidecar" -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $SidecarOut -RedirectStandardError $SidecarErr -PassThru
    Set-Content -Path $SidecarPidFile -Value $sidecar.Id
} catch {
    Show-LifeOSError "Life OS assistant failed" ("Could not start the desktop assistant." + $NL + $NL + $_.Exception.Message)
    exit 1
}

Start-Sleep -Seconds 2
$sidecar.Refresh()
if ($sidecar.HasExited) {
    $detail = Tail-OrEmpty $SidecarErr
    Show-LifeOSError "Life OS assistant crashed" ("The side assistant exited immediately." + $NL + $NL + $detail + $NL + $NL + "Logs are in:" + $NL + $StateDir + $NL + $NL + "Run windows\doctor.ps1 for a full check.")
    exit 1
}
