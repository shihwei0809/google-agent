@echo off
chcp 65001 >nul
echo ==================================================
echo 🚀 準備部署 QC 系統至 Cloudflare Pages + D1
echo ==================================================
powershell -ExecutionPolicy Bypass -File "%~dp0setup_env.ps1"
echo.
echo 部署流程已結束，請按任意鍵關閉視窗。
pause >nul
