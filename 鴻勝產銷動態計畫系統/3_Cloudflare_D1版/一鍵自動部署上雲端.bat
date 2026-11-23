@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================================
echo   Deploy Sales Planner PWA to Cloudflare Pages + D1
echo ========================================================

set NODE_OPTIONS=--use-system-ca

set STAGE=%TEMP%\sales_planner_cf_stage
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%"
xcopy /E /I /Y "public" "%STAGE%\public" >nul
xcopy /E /I /Y "functions" "%STAGE%\functions" >nul
copy /Y "wrangler.toml" "%STAGE%\" >nul
copy /Y "schema.sql" "%STAGE%\" >nul

pushd "%STAGE%"
echo [1/2] Applying D1 schema to remote sales-planner-db...
call npx wrangler d1 execute sales-planner-db --remote --file=schema.sql
if errorlevel 1 (
    echo [ERROR] D1 schema execution failed!
    popd
    pause
    exit /b 1
)

echo [2/2] Deploying Cloudflare Pages (sales-planner-pwa)...
call npx wrangler pages deploy public --project-name sales-planner-pwa --branch main --commit-dirty=true
set DEPLOY_ERR=%ERRORLEVEL%
popd

if not "%DEPLOY_ERR%"=="0" (
    echo [ERROR] Pages deployment failed!
    pause
    exit /b 1
)

echo ========================================================
echo   SUCCESS! Live at: https://sales-planner-pwa.pages.dev
echo ========================================================
pause
