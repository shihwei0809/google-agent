@echo off
chcp 65001 >nul
title 三合一單與 COA 四重核對 PWA - 本機啟動器
echo ===================================================
echo   三合一單與 COA 核對系統 PWA (本機測試伺服器)
echo ===================================================
echo.

:: 檢查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 找不到 Python，請先安裝 Python 3.8 以上版本！
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 啟動伺服器
echo 🚀 正在啟動智慧 Web 伺服器 (具備自動 Port 切換與區網 IP 顯示)...
python run_server.py

pause
