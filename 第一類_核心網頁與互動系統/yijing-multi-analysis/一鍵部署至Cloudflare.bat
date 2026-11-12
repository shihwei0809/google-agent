@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo [易見｜多重命理分析] 正在部署至 Cloudflare Workers
echo ========================================================
echo.

:: 自動設定 API Token (若本機環境變數未設定，由 wrangler 登入態提供)
if "%CLOUDFLARE_ACCOUNT_ID%"=="" (
    set CLOUDFLARE_ACCOUNT_ID=7bf430fb55af9ca6c91aba8997fc841d
)

call npx wrangler deploy
echo.

if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo [SUCCESS] 部署成功！
    echo 🌟 正式網址: https://yijing-multi-analysis.shihwei0809.workers.dev
    echo ========================================================
    start https://yijing-multi-analysis.shihwei0809.workers.dev
) else (
    echo ========================================================
    echo [ERROR] 部署失敗，請檢查網路連線。
    echo ========================================================
)
pause
