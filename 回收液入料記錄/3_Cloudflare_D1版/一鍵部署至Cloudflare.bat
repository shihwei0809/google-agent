@echo off
chcp 65001 >nul 2>&1
title 正在部署回收液入料記錄至 Cloudflare Pages...
set NODE_OPTIONS=--use-system-ca
set "SRC=%~dp0"
set "STAGE=%TEMP%\recycle_portal_cf_stage"
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%"
echo [1/3] 正在打包前端靜態資產至暫存目錄...
xcopy "%SRC%public" "%STAGE%\public\" /E /I /Q >nul
echo [2/3] 正在打包後端 Functions API...
xcopy "%SRC%functions" "%STAGE%\functions\" /E /I /Q >nul
copy /y "%SRC%wrangler.toml" "%STAGE%\wrangler.toml" >nul

echo [3/3] 正在發布至 Cloudflare Pages (recycle-portal)...
pushd "%STAGE%"
call npx wrangler pages deploy ./public --project-name=recycle-portal --commit-dirty=true
popd

echo.
echo ============================================================
echo   部署完成！線上網址: https://recycle-portal.pages.dev
echo ============================================================
if exist "%STAGE%" rmdir /s /q "%STAGE%"
pause
