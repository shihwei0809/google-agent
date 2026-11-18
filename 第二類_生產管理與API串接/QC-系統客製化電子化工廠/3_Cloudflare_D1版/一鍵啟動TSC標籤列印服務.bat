@echo off
title TSC Print Service
cd /d "%~dp0"
echo Starting TSC Print Proxy Service...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tsc_print_proxy.ps1"
pause
