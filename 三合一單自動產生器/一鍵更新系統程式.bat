@echo off
cd /d "%~dp0"

:: 1. 檢查是否在網路磁碟機 (如 NAS) 或 UNC 網路路徑上執行
if "%~d0"=="" goto ON_NAS
net use %~d0 >nul 2>&1
if %errorlevel% == 0 goto ON_NAS

:: 2. 檢查本機電腦是否有安裝 Git
git --version >nul 2>&1
if errorlevel 1 goto MISSING_GIT

:: 3. 本機執行 Git 雲端更新
echo ==================================================
echo 正在從雲端更新系統程式...
echo ==================================================

if exist "%~dp0.git" (
    git pull
) else (
    cd ..
    git pull
)

echo.
echo ==================================================
echo 更新完成！正在自動為您開啟系統...
echo ==================================================
ping 127.0.0.1 -n 3 >nul
goto START_APP

:ON_NAS
echo ==================================================
echo 【提醒】此「一鍵更新系統程式」不適合在 NAS 上執行！
echo 請在本機執行完後，再自行將最新檔案更新至 NAS。
echo ==================================================
echo.
echo 正在直接為您啟動主程式...
ping 127.0.0.1 -n 3 >nul
goto START_APP

:START_APP
cd /d "%~dp0"
start 啟動_三合一單產生器.bat
exit

:MISSING_GIT
echo.
echo ==================================================
echo [錯誤] 您的電腦尚未安裝 Git 程式！
echo ==================================================
echo 系統將自動打開網頁，請下載並安裝「Git for Windows」。
echo 安裝時請一直按「Next」到底即可完成。
echo.
start https://git-scm.com/download/win
pause
exit