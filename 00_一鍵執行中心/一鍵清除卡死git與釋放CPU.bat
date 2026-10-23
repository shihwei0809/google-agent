@echo off
title Kill Stuck Git
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0kill_git.ps1"
echo.
pause
