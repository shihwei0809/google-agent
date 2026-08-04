@echo off
title FastAPI AI API Server - Quick Start
cd /d "%~dp0api_server"

echo ==========================================================
echo           FastAPI AI Server Quick Start
echo ==========================================================
echo.

:: 1. Check if venv python exists
if exist "venv\Scripts\python.exe" (
    echo [INFO] Virtual environment found. Activating...
    call venv\Scripts\activate.bat
    goto START_SERVER
)

:: 2. If venv does not exist, look for global python
echo [INFO] Virtual environment not found. Checking Python...
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto CREATE_VENV
)

:: Check common installation paths
if exist "C:\Python313\python.exe" (
    set PYTHON_CMD=C:\Python313\python.exe
    goto CREATE_VENV
)
if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    goto CREATE_VENV
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto CREATE_VENV
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto CREATE_VENV
)

echo [ERROR] Python was not found on your system.
echo [ERROR] Please install Python and add it to your PATH.
pause
exit /b

:CREATE_VENV
echo [INFO] Creating virtual environment using %PYTHON_CMD%...
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b
)
echo [INFO] Virtual environment created successfully.
echo [INFO] Installing requirements...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install packages.
    pause
    exit /b
)
echo [INFO] Requirements installed successfully.

:START_SERVER
:: Set PYTHONPATH
set PYTHONPATH=%cd%

echo.
echo ==========================================================
echo  FastAPI started successfully!
echo  - Swagger UI (API test): http://127.0.0.1:8000/docs
echo  - Health Check API: http://127.0.0.1:8000/
echo ==========================================================
echo.
echo  Press Ctrl + C to stop the server.
echo.

python -m uvicorn app.main:app --reload

pause
