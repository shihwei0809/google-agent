@echo off
chcp 65001 >nul
title SOP / WI 電子化檢點系統 - PWA 本機伺服器
cd /d "%~dp0"

echo [1/3] 偵測 Python 環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未偵測到 Python，將自動開啟官方下載頁...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/3] 檢查必要目錄...
if not exist "icons" mkdir "icons"

echo [3/3] 啟動 PWA 本機伺服器（自動偵測 Port 與區網 IP）...
python run_server.py
pause
