@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo [易見｜多重命理分析] 正在部署至 Cloudflare Workers
echo ========================================================
echo.

call npx --yes wrangler deploy
echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo [SUCCESS] 部署成功！
    echo 🌟 正式網址: https://yijing-multi-analysis.shihwei0809.workers.dev
    echo ========================================================
    start https://yijing-multi-analysis.shihwei0809.workers.dev
) else (
    echo ========================================================
    echo [提示] 偵測到 Cloudflare 授權可能需要重新驗證，正在開啟瀏覽器登入...
    echo ========================================================
    call npx --yes wrangler login
    echo.
    echo 正在使用新授權進行部署...
    call npx --yes wrangler deploy
    if %ERRORLEVEL% EQU 0 (
        echo [SUCCESS] 部署成功！
        start https://yijing-multi-analysis.shihwei0809.workers.dev
    )
)
pause
