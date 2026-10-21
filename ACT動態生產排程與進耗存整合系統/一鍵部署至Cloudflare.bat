@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo [ACT 動態生產排程與進耗存整合系統] 一鍵部署至 Cloudflare Pages
echo ========================================================
echo.

rem 優先載入本目錄 .env 或父級 .env，支援無人值守自動部署
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)
if "%NODE_TLS_REJECT_UNAUTHORIZED%"=="" set NODE_TLS_REJECT_UNAUTHORIZED=0

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
    echo [提示] 偵測到 Cloudflare 授權憑證可能已過期，正在為您開啟瀏覽器登入...
    echo ========================================================
    call npx --yes wrangler login
    echo.
    echo 正在使用新授權進行部署...
    call npx --yes wrangler pages deploy public --project-name act-planner-pwa --no-bundle --commit-dirty=true
    if %ERRORLEVEL% EQU 0 (
        echo ========================================================
        echo [SUCCESS] 部署成功！
        echo 線上網址: https://act-planner-pwa.pages.dev
        echo ========================================================
        start https://act-planner-pwa.pages.dev
    ) else (
        echo ========================================================
        echo [FAILED] 部署仍未完成，請確認網路連線或登入狀態。
        echo ========================================================
    )
)

echo.
pause
