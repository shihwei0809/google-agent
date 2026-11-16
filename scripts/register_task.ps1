$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File `"d:\GOOGLE ANGET\scripts\clean_stuck_git.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 7:30am
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "AutoClean_Stuck_Git" -Action $action -Trigger $trigger -Settings $settings -Force | Select-Object TaskName, State
