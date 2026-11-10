@echo off
chcp 65001 >nul
title 三合一單與 COA 核對系統 - Cloudflare Pages 自動部署
cd /d "%~dp0"

echo ===================================================
echo   Cloudflare Pages 一鍵自動發布 (Cloud + R2 PWA)
echo ===================================================
echo.

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 找不到 Node.js，請先安裝 Node.js 環境！
    pause
    exit /b 1
)

echo 正在透過 Cloudflare 官方 API 自動編譯與發布至 Pages...
node --use-system-ca deploy_pages.js

if %errorlevel% neq 0 (
    echo.
    echo ❌ 發布失敗，請檢查網路連線或 API Token！
) else (
    echo.
    echo ===================================================
    echo ✅ Cloudflare Pages 雲端發布完成！
    echo 🔗 網址: https://coa-check-pwa.pages.dev
    echo ===================================================
)
pause
