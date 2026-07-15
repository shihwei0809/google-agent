@echo off
title PDF to Video Web Server
echo ============================================================
echo   DeckEdit Video - 簡報語音影片生成器
echo   正在啟動本機網頁伺服器，請稍候...
echo ============================================================
echo.

:: 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [-] 錯誤：找不到 Python！請確認系統已安裝 Python 3.9+ 且已加入環境變數。
    pause
    exit /b
)

:: 自動開啟瀏覽器
timeout /t 3 /nobreak >nul
start http://localhost:8002/

:: 啟動網頁伺服器
python video_web_app.py --port 8002

pause
