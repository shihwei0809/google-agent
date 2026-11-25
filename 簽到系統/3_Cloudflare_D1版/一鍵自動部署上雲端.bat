@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ====================================================
echo   企業活動簽到系統 - Cloudflare Pages + D1 一鍵部署
echo ====================================================
echo.
echo [1/2] 套用 D1 資料表結構 (event-checkin-db)...
call npx wrangler d1 execute event-checkin-db --remote --file=schema.sql --yes
if %errorlevel% neq 0 (
  echo [錯誤] D1 Schema 套用失敗，請確認已執行 npx wrangler login
  pause
  exit /b 1
)
echo.
echo [2/2] 部署至 Cloudflare Pages (event-checkin-system)...
call npx wrangler pages deploy public --project-name=event-checkin-system --branch=main --commit-dirty=true
echo.
echo ====================================================
echo   正式網址：https://event-checkin-system.pages.dev
echo ====================================================
pause
