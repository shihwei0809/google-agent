@echo off
chcp 65001 > nul
echo ==================================================
echo Starting PWA System...
echo ==================================================
cd /d "%~dp0"
python run_server.py
pause
