@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ============================================================
echo   鴻勝資材部季年報智慧分析系統 — Cloudflare Pages + D1 部署
echo ============================================================
echo.
powershell -ExecutionPolicy Bypass -File "..\setup_env.ps1" -DeployCloudflare
pause
