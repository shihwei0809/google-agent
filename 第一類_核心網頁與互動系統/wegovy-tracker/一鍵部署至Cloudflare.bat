@echo off
chcp 65001 >nul
title 部署 Wegovy 施打與體重紀錄至 Cloudflare Pages
color 0b

echo ========================================================
echo    🚀 正在部署 Wegovy 紀錄系統至 Cloudflare Pages...
echo    專案名稱: wegovy-tracker
echo    線上網址: https://wegovy-tracker.pages.dev
echo ========================================================
echo.

npx wrangler pages deploy public --project-name=wegovy-tracker --commit-dirty=true

echo.
echo ========================================================
echo [✔] 部署完成！請開啟下方網址確認：
echo     https://wegovy-tracker.pages.dev
echo ========================================================
pause
