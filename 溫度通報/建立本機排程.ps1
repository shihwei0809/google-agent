# Windows 工作排程器一鍵安裝腳本 (環境溫度監控通報系統)
# 使用方法：請在該檔案按右鍵，選擇「使用 PowerShell 執行」（需要管理員權限）

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $ScriptDir "weather_monitor.py"

if (-not (Test-Path $ScriptPath)) {
    Write-Error "找不到 weather_monitor.py，請確認此腳本與 weather_monitor.py 放在同一個資料夾下！"
    pause
    Exit
}

# 優先尋找 pythonw.exe (無視窗背景執行版) 以免彈出 CMD 視窗，若找不到則退回 python.exe
$PythonExe = "pythonw"
$wherePython = where.exe pythonw 2>$null
if (-not $wherePython) {
    $wherePython = where.exe python 2>$null
    if ($wherePython) {
        $PythonExe = $wherePython[0]
    } else {
        Write-Error "找不到 pythonw.exe 或 python.exe，請確認這台電腦已安裝 Python 並加入環境變數！"
        pause
        Exit
    }
} else {
    $PythonExe = $wherePython[0]
}

Write-Host "偵測到 Python 執行檔路徑: $PythonExe" -ForegroundColor Cyan
Write-Host "偵測到監控腳本路徑: $ScriptPath" -ForegroundColor Cyan

# 建立 Windows 工作排程 (以 SYSTEM 身分在背景默默執行，不彈出視窗)
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ScriptPath -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Daily -At "07:58"
$Trigger.Repetition = (New-Object -TypeName Microsoft.PowerShell.Cmdletization.GeneratedTypes.ScheduledTask.RepetitionPattern)
$Trigger.Repetition.Interval = "PT1H" # 每 1 小時重複一次 (本機程式會自動判斷頻率節流)
$Trigger.Repetition.Duration = "P1D"   # 重複 1 天 (每天重複)

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances Parallel
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

Register-ScheduledTask -TaskName "環境溫度監控通報系統" -Action $Action -Trigger $Trigger -Settings $settings -Principal $Principal -Force

Write-Host "--------------------------------------------------" -ForegroundColor Green
Write-Host "【成功】環境溫度監控排程任務已成功建立！" -ForegroundColor Green
Write-Host "本機將在每天 08:00 - 24:00 之間自動於背景執行，並依設定頻率進行監控。" -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Green
pause
