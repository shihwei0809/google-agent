@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo Deploying to Cloudflare Pages...
echo ========================================================
echo.
call npx --yes wrangler pages deploy public --project-name ipa-pwa-app --commit-dirty=true
echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo [SUCCESS] https://ipa-pwa-app.pages.dev
    echo ========================================================
) else (
    echo ========================================================
    echo [FAILED] Deployment failed. Please check error.
    echo ========================================================
)
echo.
pause
