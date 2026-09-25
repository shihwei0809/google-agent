@echo off
chcp 65001 >nul
echo ==========================================
echo [Start] Cloudflare Pages + D1 Deploy
echo ==========================================
set CLOUDFLARE_API_TOKEN=
set CLOUDFLARE_ACCOUNT_ID=
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_env.ps1"
echo.
echo [Finish] Please check the output above.
pause