@echo off
chcp 65001 >nul
echo 正在偵測 Python 路徑...
where python > temp_py.txt 2>nul
if errorlevel 1 (
    echo [錯誤] 找不到 python 執行檔，請確認這台電腦已安裝 Python 並加入環境變數！
    del temp_py.txt 2>nul
    pause
    exit /b
)

set /p PY_PATH=<temp_py.txt
del temp_py.txt 2>nul
echo 偵測到 Python: %PY_PATH%

set SCRIPT_PATH=%~dp0weather_monitor.py
echo 偵測到監控腳本: %SCRIPT_PATH%

echo.
echo 正在建立 Windows 工作排程 (WeatherMonitor)...
schtasks /create /tn "WeatherMonitor" /tr "\"%PY_PATH%\" \"%SCRIPT_PATH%\"" /sc minute /mo 10 /st 08:00 /ru "SYSTEM" /f

if errorlevel 1 (
    echo.
    echo [失敗] 建立工作排程失敗，請確認您是「右鍵 -> 以系統管理員身分執行」此批次檔！
) else (
    echo.
    echo ==================================================
    echo 【成功】工作排程 (WeatherMonitor) 已成功建立！
    echo 本機將會每 10 分鐘在背景自動偵測並執行監控。
    echo ==================================================
)
pause
