@echo off
chcp 65001 >nul
title 三合一單與 COA 核對系統 - Cloudflare 本地模擬運行
echo ===================================================
echo   啟動 Cloudflare Pages 本地模擬伺服器 (支援 Functions, D1, R2)
echo ===================================================
echo.

where npx >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 找不到 npx，請先安裝 Node.js 環境！
    pause
    exit /b 1
)

echo 啟動 wrangler pages dev public ...
call npx wrangler pages dev public --d1=DB=coa-check-db --r2=PHOTOS=coa-check-photos --port=8788
pause
