@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo [動態生產排程與進耗存整合系統] 一鍵部署至 Cloudflare Pages
echo ========================================================
echo.

node --use-system-ca deploy_pages.js

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo [SUCCESS] 部署完成！雙站皆已同步更新：
    echo 🔗 https://prod-planner-pwa.pages.dev
    echo 🔗 https://act-planner-pwa.pages.dev
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo [FAILED] 部署失敗，請檢查網路連線或 API Token 設定。
    echo ========================================================
)

echo.
pause