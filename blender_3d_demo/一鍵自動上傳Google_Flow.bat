@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

title Google Flow 本機 Chrome 一鍵全自動上傳器

echo.
echo  ========================================================
echo   Google Flow 本機 Chrome 一鍵全自動上傳器 (免 API Key)
echo   使用你自己的 PRO / 免費點數，自動切換影格並上傳首尾幀
echo  ========================================================
echo.
echo   請選擇要自動上傳的風格版本：
echo     [1] 🎈 兒童卡通玩具王國版 (預設，直接按 Enter)
echo     [2] ⚡ 賽博龐克霓虹雨夜版
echo     [3] ⚔️ 奇幻武俠仙俠古街版
echo     [4] 🧊 Blender 原始白模版
echo.
set "CHOICE="
set /p "CHOICE=請輸入編號 (1-4，預設 1): "

set "THEME=kids"
if "%CHOICE%"=="2" set "THEME=cyberpunk"
if "%CHOICE%"=="3" set "THEME=wuxia"
if "%CHOICE%"=="4" set "THEME=white"

python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [環境檢查] 首次執行，正在安裝 playwright 套件...
    python -m pip install playwright -q
)

echo.
echo  正在啟動並連線本機 Chrome (主題: !THEME!)...
echo.
python auto_upload_flow.py --theme !THEME!
echo.
pause
