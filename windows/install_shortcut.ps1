$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $PSScriptRoot "start_life_os.ps1"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Life OS.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " + [char]34 + $StartScript + [char]34
$Shortcut.WorkingDirectory = $RepoRoot
$Shortcut.Description = "Start Life OS and the Windows side assistant"
$Shortcut.Save()

Write-Host "Created: $ShortcutPath" -ForegroundColor Green
Write-Host "If it ever fails silently, run windows\Debug-Life-OS.cmd."
