@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================================
echo   Sales Planner PWA - Local Server Auto Launcher
echo ========================================================

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Opening download page...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Restoring pip...
    python -m ensurepip --default-pip
)

set PKG[0]=fastapi^|fastapi>=0.100.0
set PKG[1]=uvicorn^|uvicorn>=0.22.0
set PKG[2]=openpyxl^|openpyxl>=3.1.0
set PKG[3]=docx^|python-docx>=1.1.0
set PKG_COUNT=4

set /a MAX_IDX=%PKG_COUNT%-1
for /L %%i in (0,1,%MAX_IDX%) do (
    for /f "tokens=1,2 delims=|" %%a in ("!PKG[%%i]!") do (
        python -c "import %%a" >nul 2>&1
        if errorlevel 1 (
            echo [INSTALL] Missing package %%b , installing...
            python -m pip install "%%b"
        )
    )
)

if not exist "data" mkdir "data"

echo [START] Launching FastAPI + SQLite server (Default Port 8005, Auto-Fallback)...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8005"
python run_server.py
pause
