@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo [System] Preparing AI Interview Analyzer...

:: Check virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [System] First run detected - missing dependencies.
    echo [System] Auto-installing required components, please wait...
    powershell -ExecutionPolicy Bypass -File setup_env.ps1
    if errorlevel 1 (
        echo [Error] Installation failed. Check network or setup_env.ps1.
        pause
        exit /b
    )
)

:: Activate venv and start
echo [System] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [System] Starting server...
python main.py

if errorlevel 1 (
    echo [Error] Failed. Trying fallback uvicorn...
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
)
pause