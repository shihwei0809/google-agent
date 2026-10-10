@echo off
echo ==================================================
echo 正在從雲端更新系統程式...
echo ==================================================
cd /d "%~dp0"
cd ..

git --version >nul 2>&1
if errorlevel 1 goto MISSING_GIT

git pull
echo.
echo ==================================================
echo 更新完成！正在自動為您開啟系統...
echo ==================================================

timeout /t 2 >nul
cd /d "%~dp0"
start 啟動_三合一單產生器.bat
exit

:MISSING_GIT
echo [錯誤] 您的電腦尚未安裝 Git 程式！
echo 系統將自動打開網頁，請下載並安裝「Git for Windows」。
echo 安裝時請一直按「Next」到底即可。
echo.
start https://git-scm.com/download/win
pause
exit