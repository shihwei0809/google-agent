@echo off
chcp 65001 >nul
echo ==================================================
echo 🚀 準備部署 QC 系統至 Cloudflare Pages + D1
echo ==================================================
rem 清除環境變數，強迫 Wrangler 使用網頁登入權限
set CLOUDFLARE_API_TOKEN=
set CLOUDFLARE_ACCOUNT_ID=
powershell -ExecutionPolicy Bypass -File "%~dp0setup_env.ps1"
echo.
echo 部署流程已結束，請按任意鍵關閉視窗。
pause >nul
