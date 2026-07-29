@echo off
setlocal
cd /d "%~dp0interview_analyzer"

echo [System] Preparing AI Interview Analyzer...
python main.py

if errorlevel 1 (
    echo [Error] Execution failed. Retrying with fallback uvicorn...
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
)
pause
