@echo off
cd /d "%~dp0"
chcp 65001 >nul 2>&1
echo ======================================================
echo  IPA (異丙醇) 報價與出貨單船期自動追蹤系統 - Cloudflare D1 自動部署
echo ======================================================
powershell -ExecutionPolicy Bypass -File "..\setup_env.ps1" -DeployCloudflare
pause
