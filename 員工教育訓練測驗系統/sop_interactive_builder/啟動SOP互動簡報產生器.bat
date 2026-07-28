@echo off
chcp 65001 >nul
title SOP Interactive Builder
cd /d "%~dp0"
echo =========================================================
echo  SOP Interactive Builder is starting...
echo  The browser will open automatically.
echo  Keep this window open to run the server.
echo =========================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python not found. Please install Python and add to PATH.
    pause
    exit /b
)
if not exist "venv\Scripts\python.exe" (
    echo [Setup] Creating Python virtual environment...
    python -m venv venv
)
echo [Setup] Checking and installing requirements (this may take a moment)...
venv\Scripts\python.exe -m pip install -q -r requirements.txt
if not exist "jobs" mkdir jobs
if not exist "templates" mkdir templates

cls
venv\Scripts\python.exe run_server.py
pause
