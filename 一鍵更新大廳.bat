@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 正在啟動專案大廳與說明書一鍵同步與部署...
echo ==================================================

cd /d "%~dp0"

echo [1/4] 正在編譯掃描 Markdown 說明書...
python portal_tools\compile_manuals.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 編譯說明書資料庫失敗！
    pause
    exit /b 1
)

echo [2/4] 正在打包專案大廳靜態網頁...
python portal_tools\build_portal.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 打包靜態網頁失敗！
    pause
    exit /b 1
)

echo [3/4] 正在同步推送至 GitHub 獨立大廳倉庫 (Cloudflare Pages)...
python portal_tools\push_portal.py

echo [4/4] 正在上傳 Draft 預覽版本至 Netlify...
set DEPLOY_ID=
for /f "tokens=*" %%i in ('PowerShell -Command "$env:NETLIFY_AUTH_TOKEN='nfc_ne4sMkFbBomH87HYzdqHrR4mqDPj7jwS0fdd'; npx netlify deploy --dir=說明書 --site=c0fb0f0a-10da-450f-b08d-1093ea06b78e --json | ConvertFrom-Json | Select-Object -ExpandProperty deploy_id"') do set DEPLOY_ID=%%i

if "%DEPLOY_ID%"=="" (
    echo [ERROR] 取得 Deploy ID 失敗，請確認 Netlify 連線狀態。
    pause
    exit /b 1
)
echo Draft 上傳成功！版本 ID: %DEPLOY_ID%

echo 正在將預覽版強制推廣為 Production 正式版...
set NETLIFY_AUTH_TOKEN=nfc_ne4sMkFbBomH87HYzdqHrR4mqDPj7jwS0fdd
npx netlify api restoreSiteDeploy --data "{\"site_id\": \"c0fb0f0a-10da-450f-b08d-1093ea06b78e\", \"deploy_id\": \"%DEPLOY_ID%\"}" > nul

echo ==================================================
echo 🎉 同步與部署成功！
echo ☁️ Cloudflare Pages 線上大廳：https://google-agent.pages.dev
echo 🔗 Netlify 正式網址：https://cerulean-praline-6b314d.netlify.app/
echo ==================================================
pause
