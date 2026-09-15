@echo off
chcp 65001 >nul
echo ========================================================
echo   Cloudflare Pages + D1 一鍵自動部署上雲端
echo ========================================================
echo 若您遇到瀏覽器登入失敗 (fetch failed)，請貼上您的 CLOUDFLARE_API_TOKEN。
echo 若想嘗試一般瀏覽器登入，請直接按 Enter 跳過。
echo 取得 Token 的網址: https://dash.cloudflare.com/profile/api-tokens
set /p CLOUDFLARE_API_TOKEN="請輸入 API Token (直接按 Enter 跳過): "
set NODE_TLS_REJECT_UNAUTHORIZED=0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_env.ps1"
pause

