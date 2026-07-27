import subprocess

ps_cmd = """
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"C:\\GOOGLE ANGET\\AutoSync_OffWork.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 11:00PM
Register-ScheduledTask -TaskName "AutoSync_OffWork" -Action $action -Trigger $trigger -Description "每日 23:00 自動收工 Git Commit & Push" -Force
"""

result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
