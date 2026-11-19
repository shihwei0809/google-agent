@echo off
chcp 65001 >nul
title 小包系統報表產生 (勝一專用版) - 一鍵系統更新精靈

echo ============================================================
echo      小包系統報表產生 (勝一專用版) - 一鍵系統更新精靈
echo ============================================================
echo.

cd /d "%~dp0"

:: ------------------------------------------------------------
:: 情況 1：檢查是否處於 Git 版本庫環境
:: ------------------------------------------------------------
git rev-parse --is-inside-work-tree >nul 2>&1
if "%ERRORLEVEL%"=="0" goto GIT_PULL_MODE

if exist "%~dp0..\.git" (
    cd /d "%~dp0.."
    goto GIT_PULL_MODE
)

:: ------------------------------------------------------------
:: 情況 2：無 Git 版本庫 (獨立資料夾 / 隨身碟複製版本)
:: 優先使用 curl 或 PowerShell 下載最新主程式
:: ------------------------------------------------------------
:CLOUD_DIRECT_DOWNLOAD
echo [狀態] 偵測到目前為獨立資料夾模式。
echo [動作] 正在連線 GitHub 雲端為您下載最新 main.py 主程式...
echo.

set "RAW_URL=https://raw.githubusercontent.com/shihwei0809/google-agent/main/%%E5%%B0%%8F%%E5%%8C%%85%%E7%%B3%%BB%%E7%%B5%%B1%%E5%%A0%%B1%%E8%%A1%%A8%%E7%%94%%A2%%E7%%94%%9F_%%E5%%8B%%9D%%E4%%B8%%80/main.py"

:: 優先嘗試 curl
curl.exe -fsSL "%RAW_URL%" -o "main.py.new" >nul 2>&1
if exist "main.py.new" (
    move /y "main.py.new" "main.py" >nul
    goto DOWNLOAD_OK
)

:: 備用 PowerShell 下載
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%RAW_URL%', 'main.py')" >nul 2>&1
if "%ERRORLEVEL%"=="0" goto DOWNLOAD_OK

echo [警告] 雲端直接下載失敗，請檢查網路連線是否正常。
echo 將為您嘗試啟動現有程式...
pause
goto LAUNCH_APP

:DOWNLOAD_OK
echo ============================================================
echo  [成功] 已自動從 GitHub 雲端下載最新 main.py 並完成更新！
echo ============================================================
echo.
timeout /t 2 >nul
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 情況 1 的執行流程 (Git pull，具備防呆與衝突保護)
:: ------------------------------------------------------------
:GIT_PULL_MODE
echo [狀態] 偵測到本機 Git 版本庫，正在從 GitHub 雲端同步最新版本...
echo.

:: 暫存本地可能存在的修改或暫存檔，防止 git pull 衝突中斷
git stash >nul 2>&1

:: 執行拉取
git pull origin main
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ============================================================
    echo  [成功] 雲端更新完成！本機已為最新版本。
    echo ============================================================
    echo.
    timeout /t 2 >nul
    goto LAUNCH_APP
)

:: 若普通 pull 失敗，嘗試 fetch + rebase
git fetch origin main >nul 2>&1
git rebase origin/main >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ============================================================
    echo  [成功] 雲端更新完成 (已自動對齊最新版本)！
    echo ============================================================
    echo.
    timeout /t 2 >nul
    goto LAUNCH_APP
)

echo.
echo [警告] 偵測到本地有未合併之檔案或網路不穩定。
echo 正在為您強制同步最新主程式...
git checkout origin/main -- "小包系統報表產生_勝一/main.py" >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [成功] 已成功強制同步最新 main.py！
    timeout /t 2 >nul
    goto LAUNCH_APP
)

echo [提示] 將直接為您啟動現有程式...
timeout /t 2 >nul

:: ------------------------------------------------------------
:: 啟動主程式
:: ------------------------------------------------------------
:LAUNCH_APP
cd /d "%~dp0"
if exist "啟動本機視窗版.bat" (
    start "" "啟動本機視窗版.bat"
) else (
    start "" python main.py
)
exit