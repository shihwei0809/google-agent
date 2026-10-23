@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 正在啟動專案大廳與說明書一鍵同步與部署...
echo ==================================================

cd /d "%~dp0.."

echo [1/4] 正在編譯彙整 Markdown 說明書...
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

echo [3/4] 正在同步推送至 GitHub 展示大廳倉庫 (Cloudflare Pages)...
python portal_tools\push_portal.py

echo.
echo ✅ 大廳更新完成！
pause
