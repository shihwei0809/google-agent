@echo off
chcp 65001 > nul
echo ==================================================
echo 正在從雲端 (Git) 取回最新版本的系統程式...
echo ==================================================
cd /d "%~dp0"
cd ..

:: 檢查是否有安裝 Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 您的電腦尚未安裝 Git 程式！
    echo 系統將自動開啟下載網頁，請下載並安裝「Git for Windows」。
    echo 安裝時請一直按「Next」到底即可。
    echo.
    start https://git-scm.com/download/win
    pause
    exit
)

git pull
echo.
echo ==================================================
echo 更新完成！您可以關閉此視窗，並使用「啟動本機視窗版.bat」開啟系統。
echo ==================================================
pause