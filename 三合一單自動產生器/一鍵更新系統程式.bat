@echo off
chcp 950 >nul
title 三合一單自動產生器 - 一鍵系統更新精靈

echo ============================================================
echo         三合一單自動產生器 - 一鍵系統更新精靈
echo ============================================================
echo.

cd /d "%~dp0"

:: ------------------------------------------------------------
:: 情況 1：若本資料夾屬於 Git 版本庫，直接執行正規 git pull
:: ------------------------------------------------------------
if exist "%~dp0..\.git" goto GIT_PULL_MODE
git rev-parse --is-inside-work-tree >nul 2>&1
if "%ERRORLEVEL%"=="0" goto GIT_PULL_MODE

:: ------------------------------------------------------------
:: 情況 2：無 Git 版本庫 (一般人員電腦 / NAS / 隨身碟複製資料夾)
:: 直接使用 Windows 內建工具自動從 GitHub 下載最新程式！
:: ------------------------------------------------------------
:CLOUD_DIRECT_DOWNLOAD
echo [狀態] 偵測到目前為獨立資料夾 (非 Git 本機庫)。
echo [動作] 正在自動連線 GitHub 雲端為您下載最新程式...
echo.

powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { (New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/shihwei0809/google-agent/main/%%E4%%B8%%89%%E5%%90%%88%%E4%%B8%%80%%E5%%96%%AE%%E8%%87%%AA%%E5%%8B%%95%%E7%%94%%A2%%E7%%94%%9F%%E5%%99%%A8/main.py', 'main.py'); exit 0 } catch { exit 1 }"

if errorlevel 1 (
    echo [警告] 雲端直接下載失敗，請檢查網路連線是否正常。
    echo 將為您嘗試啟動現有程式...
    pause
    goto LAUNCH_APP
)

echo ============================================================
echo  [成功] 已自動從 GitHub 雲端下載最新 main.py 並完成更新！
echo ============================================================
echo.
timeout /t 2 >nul
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 情況 1 的執行流程 (Git pull)
:: ------------------------------------------------------------
:GIT_PULL_MODE
echo [狀態] 偵測到本機 Git 開發庫，正在從 GitHub 雲端執行 git pull...
echo.

cd /d "%~dp0.."

:: 自動防呆修復：若先前有未結案的 merge (MERGE_HEAD) 導致卡死，自動重設以確保可順暢更新
if exist ".git\MERGE_HEAD" (
    echo [防呆處理] 偵測到本機有未完成的合併狀態 (MERGE_HEAD)，正在自動重設修復...
    git merge --abort >nul 2>&1
)

git pull
if errorlevel 1 (
    echo.
    echo [警告] git pull 更新失敗！請檢查網路連線或 Git 狀態。
    echo 將嘗試直接啟動現有程式...
    pause
    goto LAUNCH_APP
)

echo.
echo ============================================================
echo  [成功] 雲端更新完成！本機已為最新版本。
echo ============================================================
echo.

set NAS_DIR=O:\各單位對外\資材部對外\三合一單自動產生器
if exist "%NAS_DIR%" (
    echo ★ 偵測到公司 NAS (O 槽) 連線正常！
    set /p PUSH_NAS="是否要順便將最新程式同步發布至 NAS 共享區？(Y/N) [預設 Y]: "
    if "%PUSH_NAS%"=="" set PUSH_NAS=Y
    if /i "%PUSH_NAS%"=="Y" (
        echo 正在發布最新版本至 NAS...
        copy /y "%~dp0main.py" "%NAS_DIR%\main.py" >nul
        copy /y "%~dp0一鍵更新系統程式.bat" "%NAS_DIR%\一鍵更新系統程式.bat" >nul
        echo [成功] 已成功將最新檔案發布至 NAS 共享區！
        echo.
    )
)

timeout /t 2 >nul
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 啟動主程式
:: ------------------------------------------------------------
:LAUNCH_APP
cd /d "%~dp0"
if exist "啟動_三合一單產生器.bat" (
    start 啟動_三合一單產生器.bat
) else (
    start python main.py
)
exit
