@echo off
chcp 65001 > nul
title 部署 IPA 系統至 Cloudflare Pages

echo ========================================================
echo 🚀 正在部署 IPA 專用排程系統至 Cloudflare Pages...
echo ========================================================
echo.

cd /d "%~dp0"

echo 正在執行 wrangler pages deploy...
call npx wrangler pages deploy public --project-name ipa-pwa-app --commit-dirty=true

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo ✅ 部署成功！
    echo 網址: https://ipa-pwa-app.pages.dev
    echo ========================================================
) else (
    echo ========================================================
    echo ❌ 部署失敗，請檢查上方錯誤訊息或 Cloudflare 登入狀態。
    echo ========================================================
)

echo.
pause
