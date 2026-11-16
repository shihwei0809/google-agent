@echo off
chcp 65001 >nul 2>&1
set NODE_OPTIONS=--use-system-ca
set "SRC=%~dp0"
set "STAGE=%TEMP%\storage_rack_cf_stage"
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%"
xcopy "%SRC%public" "%STAGE%\public\" /E /I /Q >nul
xcopy "%SRC%functions" "%STAGE%\functions\" /E /I /Q >nul
copy /y "%SRC%wrangler.toml" "%STAGE%\wrangler.toml" >nul
pushd "%STAGE%"
call wrangler pages deploy ./public --project-name=storage-rack-pwa --commit-dirty=true
popd
pause
