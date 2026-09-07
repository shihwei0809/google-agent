@echo off
chcp 65001 >nul
title AI Educational Training Platform
color 0B
cd /d "%~dp0"
backend\venv\Scripts\python.exe run_platform.py
pause
