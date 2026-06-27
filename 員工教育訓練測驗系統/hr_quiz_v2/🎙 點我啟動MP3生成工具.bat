@echo off
title SOP Quiz Generator Manager
echo.
echo ============================================================
echo   SOP Quiz & Audio Management Center is launching...
echo   The browser will open automatically in 2 seconds.
echo   Keep this window open to run the server.
echo ============================================================
echo.
cd /d "%~dp0"
if exist "MP3生成工具.exe" (
    "MP3生成工具.exe"
) else (
    python mp3_generator_server.py
)
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start MP3生成工具.exe or python script.
    pause
)
