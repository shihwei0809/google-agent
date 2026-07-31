@chcp 65001 >nul
@echo off
title Family File Hub Server
cd /d "%~dp0"

echo =====================================================
echo 🚀 Starting Family File Hub Server...
echo =====================================================

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe app.py
) else (
    python app.py
)

pause
