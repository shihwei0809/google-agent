@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo [ACT 動態生產排程與進耗存整合系統] 一鍵部署至 Cloudflare Pages
echo ========================================================
echo.

call npx --yes wrangler pages deploy public --project-name act-planner-pwa --no-bundle --commit-dirty=true

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo [SUCCESS] 部署成功！
    echo 線上網址: https://act-planner-pwa.pages.dev
    echo ========================================================
    start https://act-planner-pwa.pages.dev
) else (
    echo ========================================================
    echo [FAILED] 部署失敗，請檢查網路連線或 Wrangler 授權。
    echo ========================================================
)

echo.
pause
