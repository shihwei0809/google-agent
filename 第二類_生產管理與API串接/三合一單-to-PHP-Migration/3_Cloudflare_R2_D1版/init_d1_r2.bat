@echo off
chcp 65001 >nul
title 三合一單與 COA 核對系統 - Cloudflare D1 與 R2 初始化
echo ===================================================
echo   Cloudflare D1 資料庫與 R2 儲存桶初始化精靈
echo ===================================================
echo.

echo [1/3] 正在建立 Cloudflare R2 儲存桶: coa-check-photos ...
call npx wrangler r2 bucket create coa-check-photos
echo.

echo [2/3] 正在建立 Cloudflare D1 資料庫: coa-check-db ...
call npx wrangler d1 create coa-check-db
echo.
echo ⚠️ 請注意：若上一步輸出了 database_id，請將其複製並填入 wrangler.toml 的 database_id 中！
echo.

echo [3/3] 正在套用資料表結構 (schema.sql) 至 D1 資料庫 ...
call npx wrangler d1 execute coa-check-db --file=./schema.sql --remote
echo.

echo ===================================================
echo ✅ 初始化完成！接著可執行「一鍵自動部署上雲端.bat」
echo ===================================================
pause
