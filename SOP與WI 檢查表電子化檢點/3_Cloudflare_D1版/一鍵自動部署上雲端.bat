@echo off
chcp 65001 >nul
title SOP / WI 電子化檢點系統 - 一鍵部署至 Cloudflare Pages + D1
cd /d "%~dp0"

echo [1/3] 檢查 wrangler CLI...
where wrangler >nul 2>&1
if errorlevel 1 (
    echo 正在安裝 wrangler...
    call npm install -g wrangler
)

echo [2/3] 套用 D1 資料庫結構 (schema.sql -> 共用主庫 hs-material-report-db)...
call wrangler d1 execute hs-material-report-db --remote --file=schema.sql --yes

echo [3/3] 部署前端與 Pages Functions 至 Cloudflare Pages...
call wrangler pages deploy public --project-name=wi-checklist-system
pause
