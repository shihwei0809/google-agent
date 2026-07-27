@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 正在啟動專案大廳 Netlify 免綁卡一鍵部署...
echo ==================================================

cd /d "C:\GOOGLE ANGET"

echo [1/3] 正在編譯打包靜態網頁...
python portal_tools\build_portal.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 打包靜態網頁失敗！
    pause
    exit /b 1
)

echo [2/3] 正在上傳 Draft 預覽版本...
set DEPLOY_ID=
for /f "tokens=*" %%i in ('PowerShell -Command "$env:NETLIFY_AUTH_TOKEN='nfc_ne4sMkFbBomH87HYzdqHrR4mqDPj7jwS0fdd'; netlify deploy --dir=說明書 --json | ConvertFrom-Json | Select-Object -ExpandProperty deploy_id"') do set DEPLOY_ID=%%i

if "%DEPLOY_ID%"=="" (
    echo [ERROR] 取得 Deploy ID 失敗，請確認 Netlify 連線狀態。
    pause
    exit /b 1
)
echo >> Draft 上傳成功！版本 ID: %DEPLOY_ID%

echo [3/3] 正在將預覽版強制推廣為 Production 正式版...
set NETLIFY_AUTH_TOKEN=nfc_ne4sMkFbBomH87HYzdqHrR4mqDPj7jwS0fdd
netlify api restoreSiteDeploy --data "{\"site_id\": \"c0fb0f0a-10da-450f-b08d-1093ea06b78e\", \"deploy_id\": \"%DEPLOY_ID%\"}" > nul

echo ==================================================
echo 🎉 部署成功！
echo 🔗 正式網址：https://cerulean-praline-6b314d.netlify.app/
echo ==================================================
pause
