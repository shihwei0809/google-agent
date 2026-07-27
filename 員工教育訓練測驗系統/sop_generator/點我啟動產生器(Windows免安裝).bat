@echo off
title Start SOP Quiz Generator Manager
echo ============================================================
echo   SOP Quiz Generator Manager is starting...
echo   The browser will open automatically in 2 seconds.
echo   Keep this window open to run the server.
echo ============================================================
cd /d "%~dp0"
start http://localhost:18082/index.html
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_intranet.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start server.
    pause
)
