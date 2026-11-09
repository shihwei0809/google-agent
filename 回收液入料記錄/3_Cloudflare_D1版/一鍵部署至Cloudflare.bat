@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title 正在部署回收液入料記錄至 Cloudflare Pages...

echo.
echo ============================================================
echo   正在部署至 recycle-portal.pages.dev ...
echo ============================================================
echo.

npx wrangler pages deploy public --project-name recycle-portal --commit-dirty=true

echo.
echo ============================================================
echo   部署完成！線上網址: https://recycle-portal.pages.dev
echo ============================================================
pause
