# Check Administrator rights
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️ This script requires Administrator privileges. Requesting UAC elevation..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "SilentlyContinue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "📅 Set Up Anti-Gravity Monthly Backup Scheduler" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$taskName = "AntiGravity_Monthly_Backup"
$batPath = "C:\GOOGLE ANGET\一鍵備份技能.bat"

if (-not (Test-Path $batPath)) {
    Write-Host "Error: Could not find backup script at $batPath!" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

# Define Action
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""

# Define Trigger (Monthly on the 1st of every month at 12:00 PM)
# Note: For wider compatibility with PowerShell 5.1 on client OS, we define trigger monthly.
$trigger = New-ScheduledTaskTrigger -Monthly -At 12:00PM -DaysOfMonth 1

# Define Settings (Allow run on battery, wake to run, etc.)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register Task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Auto-backup Anti-Gravity skills and settings to Google Drive monthly." -Force | Out-Null

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Write-Host "🎉 Monthly backup task '$taskName' registered successfully!" -ForegroundColor Green
    Write-Host "The task will run automatically at 12:00 PM on the 1st of every month." -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to register the scheduled task. Please check system permissions." -ForegroundColor Red
}

Read-Host "Press Enter to exit..."
