@echo off
title PDF Video Generator
echo.
echo ==========================================
echo    PDF Video Generator (Port 8002)
echo    Please open in your browser:
echo    http://localhost:8002
echo ==========================================
echo.
cd /d "%~dp0"
python app.py
pause
