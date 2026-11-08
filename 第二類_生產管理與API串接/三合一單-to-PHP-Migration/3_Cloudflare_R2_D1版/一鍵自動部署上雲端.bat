@echo off
chcp 65001 >nul
title 三合一單與 COA 核對系統 - Cloudflare Pages 自動部署
echo ===================================================
echo   Cloudflare Pages 一鍵自動發布 (Cloud + R2 PWA)
echo ===================================================
echo.

echo 正在檢查 Node.js 與 Wrangler...
where npx >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 找不到 npx，請先安裝 Node.js 環境！
    pause
    exit /b 1
)

echo.
echo [1/2] 正在套用本機 D1 結構到雲端 D1 (以防新欄位未同步)...
call npx wrangler d1 execute coa-check-db --file=./schema.sql --remote

echo.
echo [2/2] 正在部署至 Cloudflare Pages...
call npx wrangler pages deploy public --project-name=coa-check-pwa

echo.
echo ===================================================
echo ✅ Cloudflare Pages 雲端部署完成！
echo ===================================================
pause
