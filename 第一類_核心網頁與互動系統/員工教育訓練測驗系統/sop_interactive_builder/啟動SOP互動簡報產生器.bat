@echo off
cd /d "%~dp0"
echo [System] Starting SOP Interactive Builder...
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
echo [Setup] Installing requirements...
venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist "jobs" mkdir jobs
if not exist "templates" mkdir templates
echo [System] Started Successfully! Opening browser...
start http://localhost:8000
venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
pause
