@echo off
cd /d "%~dp0"

:: 檢查上一層是否有 Git 版本庫 (非 Git 庫如 NAS 則直接啟動)
if not exist "%~dp0..\.git" goto START_APP

echo ==================================================
echo 正在從雲端更新系統程式...
echo ==================================================
cd ..
git --version >nul 2>&1
if errorlevel 1 goto START_APP

git pull
echo.
echo ==================================================
echo 更新完成！正在自動為您開啟系統...
echo ==================================================
ping 127.0.0.1 -n 2 >nul

:START_APP
cd /d "%~dp0"
start 啟動本機視窗版.bat
exit