@echo off
title PDF Voice Cloning Video Generator
echo.
echo ==========================================
echo    PDF Voice Cloning Video Generator (Port 8003)
echo    Please open in your browser:
echo    http://localhost:8003
echo ==========================================
echo.
cd /d "%~dp0"
python app.py
pause
