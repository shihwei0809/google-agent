@echo off
title Start Local Intranet Server
echo ============================================================
echo   Starting local intranet server, please wait...
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_intranet.ps1"
pause