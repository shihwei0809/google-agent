@echo off
chcp 65001 >nul 2>&1
echo [INFO] 正在移除 Windows 開機自動啟動...
set "TARGET_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%TARGET_DIR%\啟動HTTPS遠端穿透.lnk"

if exist "%SHORTCUT_PATH%" (
    del /f /q "%SHORTCUT_PATH%"
    echo [成功] 已成功移除開機自動啟動！
) else (
    echo [提示] 目前未設定開機自動啟動。
)
pause
