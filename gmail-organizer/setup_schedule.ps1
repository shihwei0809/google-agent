# setup_schedule.ps1 - Schedule Gmail Organizer to run every 2 weeks

# Check Administrator rights
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️ This script requires Administrator privileges. Requesting UAC elevation..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "SilentlyContinue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "📅 Set Up Gmail Organizer Biweekly Scheduler" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$taskName = "Gmail_Organizer_Biweekly"
$batPath = "$PSScriptRoot\run_organizer.bat"

if (-not (Test-Path $batPath)) {
    Write-Host "Error: Could not find run script at $batPath!" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

# Define Action
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""

# Define Trigger (Weekly, interval 2 weeks, on Sunday at 10:00 AM)
$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 2 -DaysOfWeek Sunday -At 10:00AM

# Define Settings (Allow run on battery, start when available, etc.)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register Task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Automatically categorize and archive Gmail inbox emails every 2 weeks." -Force | Out-Null

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Write-Host "🎉 Biweekly organizer task '$taskName' registered successfully!" -ForegroundColor Green
    Write-Host "The task will run automatically every 2 weeks on Sunday at 10:00 AM." -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to register the scheduled task. Please check system permissions." -ForegroundColor Red
}

Read-Host "Press Enter to exit..."
