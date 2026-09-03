@echo off
chcp 65001 >nul
title AI Training Platform Launcher
color 0B

echo ===================================================
echo Starting AI Training Platform...
echo ===================================================
echo.

echo [1/3] Starting FastAPI Backend (Port: 8000)...
cd backend
start /b cmd /c "venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"
cd ..

timeout /t 2 /nobreak >nul

echo [2/3] Starting React Frontend...
cd frontend
start /b cmd /c "npm run dev -- --host"
cd ..

timeout /t 3 /nobreak >nul

echo [3/3] Opening browser...
start http://localhost:5173

echo.
echo ===================================================
echo Platform Started in Background!
echo Please keep this window open. 
echo To stop the servers, press Ctrl+C or close this window.
echo ===================================================
pause >nul
