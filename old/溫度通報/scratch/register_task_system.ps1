# Windows Task Scheduler registration script for Weather Monitor (SYSTEM account)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $ScriptDir "weather_monitor.py"

$pyw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pyw) {
    $pyw = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $pyw) {
    Write-Error "Python executable not found!"
    Exit
}
if (-not (Test-Path $ScriptPath)) {
    Write-Error "weather_monitor.py not found at $ScriptPath"
    Exit
}

$Action = New-ScheduledTaskAction -Execute $pyw -Argument "`"$ScriptPath`"" -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Once -At "00:08" -RepetitionInterval (New-TimeSpan -Minutes 10)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances Parallel
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

Register-ScheduledTask -TaskName "WeatherMonitorSystem" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force
Write-Host "=================================================="
Write-Host "SUCCESS: Scheduled task registered under SYSTEM account!"
Write-Host "Task Name: WeatherMonitorSystem"
Write-Host "Script Path: $ScriptPath"
Write-Host "=================================================="
