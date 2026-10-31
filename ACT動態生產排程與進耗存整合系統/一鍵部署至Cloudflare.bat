@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo [動態生產排程與進耗存整合系統] 一鍵部署至 Cloudflare Pages
echo ========================================================
echo.

rem 優先載入本目錄 .env 或父級 .env，支援無人值守自動部署
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)
if "%NODE_TLS_REJECT_UNAUTHORIZED%"=="" set NODE_TLS_REJECT_UNAUTHORIZED=0

echo 🚀 [1/2] 正在部署至新主要網址 [prod-planner-pwa] ...
call npx --yes wrangler pages deploy public --project-name prod-planner-pwa --no-bundle --commit-dirty=true
set DEPLOY_MAIN_STATUS=%ERRORLEVEL%

echo.
echo 🔄 [2/2] 正在同步部署至相容舊網址 [act-planner-pwa] (確保舊連結/書籤不失效) ...
call npx --yes wrangler pages deploy public --project-name act-planner-pwa --no-bundle --commit-dirty=true
set DEPLOY_OLD_STATUS=%ERRORLEVEL%

echo.
if %DEPLOY_MAIN_STATUS% EQU 0 (
    echo ========================================================
    echo [SUCCESS] 部署成功！雙網址皆已同步發布：
    echo 🌟 新版正式網址: https://prod-planner-pwa.pages.dev
    echo 🔗 相容舊版網址: https://act-planner-pwa.pages.dev (自動無縫導向新網址)
    echo ========================================================
    start https://prod-planner-pwa.pages.dev
) else (
    echo ========================================================
    echo [提示] 偵測到 Cloudflare 授權可能需要重新驗證，正在開啟瀏覽器登入...
    echo ========================================================
    call npx --yes wrangler login
    echo.
    echo 正在使用新授權進行部署...
    call npx --yes wrangler pages deploy public --project-name prod-planner-pwa --no-bundle --commit-dirty=true
    call npx --yes wrangler pages deploy public --project-name act-planner-pwa --no-bundle --commit-dirty=true
    if %ERRORLEVEL% EQU 0 (
        echo ========================================================
        echo [SUCCESS] 部署成功！
        echo 🌟 新版正式網址: https://prod-planner-pwa.pages.dev
        echo ========================================================
        start https://prod-planner-pwa.pages.dev
    ) else (
        echo ========================================================
        echo [FAILED] 部署仍未完成，請確認網路連線或登入狀態。
        echo ========================================================
    )
)

echo.
pause
