@echo off
chcp 65001 >nul
title ShinyChem Schedule Management System - Launcher
cd /d "%~dp0"

echo ============================================================
echo   Starting ShinyChem Schedule Management System...
echo ============================================================

rem 1. Check Node.js dependencies
if not exist "node_modules" (
    echo [System] Installing Node.js dependencies...
    call npm install
)

rem 2. Check Python dependencies
python -c "import openpyxl, qrcode, PIL" 2>nul
if errorlevel 1 (
    echo [System] Installing Python libraries...
    python -m pip install openpyxl qrcode pillow
)

echo ============================================================
echo   Server started successfully!
echo   Local URL: http://localhost:3000
echo ============================================================

rem Open browser in 2 seconds
ping 127.0.0.1 -n 3 >nul
start http://localhost:3000

rem Start Node.js server
node "%~dp0server.js"
pause
