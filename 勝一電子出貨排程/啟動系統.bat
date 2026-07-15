@echo off
title Win-Scheduler-Startup

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Elevating privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:: Change to the current directory of the batch file
cd /d "%~dp0"

echo ===================================================
echo   System is starting...
echo   URL: http://localhost:3000
echo ===================================================
echo.

:: Open browser in background after 2 seconds
start /b cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:3000"

:: Start the server
npm run dev

if %errorlevel% neq 0 (
    echo.
    echo Warning: Service stopped or error occurred!
    pause
)
