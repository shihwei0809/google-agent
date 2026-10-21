@echo off
chcp 65001 >nul 2>&1
echo [INFO] 正在將 HTTPS 遠端網頁穿透中心加入 Windows 開機自動啟動...
set "TARGET_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%TARGET_DIR%\啟動HTTPS遠端穿透.lnk"
set "VBS_PATH=D:\GOOGLE ANGET\HTTPS遠端網頁穿透中心\run_silent.vbs"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%VBS_PATH%\"'; $s.WorkingDirectory = 'D:\GOOGLE ANGET\HTTPS遠端網頁穿透中心'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo ============================================================
    echo [成功] 已成功註冊開機自動啟動！
    echo 電腦每次開機時，將自動在背景靜默啟動穿透服務。
    echo 最新穿透網址會自動同步至：
    echo  - G:\我的雲端硬碟\最新遠端穿透網址.html
    echo ============================================================
) else (
    echo [失敗] 無法建立開機啟動捷徑。
)
pause
