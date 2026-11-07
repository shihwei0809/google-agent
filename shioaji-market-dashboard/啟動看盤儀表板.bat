@echo off
cd /d "%~dp0"
title Shioaji Trading Terminal

echo ========================================================
echo   Shioaji Trading Terminal (AGY Edition)
echo ========================================================
echo.
echo Starting server...
echo.

python server.py

if errorlevel 1 (
    echo.
    echo Server stopped with error.
    pause
)
