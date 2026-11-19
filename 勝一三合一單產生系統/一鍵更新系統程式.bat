@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title 勝一三合一單產生系統 - 一鍵系統更新精靈 (含自動備份保護)

echo ============================================================
echo         勝一三合一單產生系統 - 一鍵系統更新精靈
echo ============================================================
echo.

cd /d "%~dp0"

:: ------------------------------------------------------------
:: 步驟 0：更新前強制自動備份現有 main.py (雙重備份：上一版 + 時間戳記歷史庫)
:: ------------------------------------------------------------
if exist "main.py" (
    for %%A in ("main.py") do set "MAIN_SIZE=%%~zA"
    if !MAIN_SIZE! GTR 5000 (
        if not exist "backups" mkdir "backups"
        set "TS=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
        set "TS=!TS: =0!"
        for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "TS=%%t"
        copy /y "main.py" "main_backup_last.py" >nul
        copy /y "main.py" "backups\main_backup_!TS!.py" >nul
        echo [安全備份] 已將更新前版本備份為：
        echo            1. main_backup_last.py ^(供「一鍵還原上一版程式.bat」即時還原^)
        echo            2. backups\main_backup_!TS!.py ^(歷史版本留存^)
        echo.
    )
)

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
:: 先下載至暫存檔 main.py.new，驗證完整性通過後才覆蓋 main.py
:: ------------------------------------------------------------
:CLOUD_DIRECT_DOWNLOAD
cd /d "%~dp0"
echo [狀態] 偵測到目前為獨立資料夾模式。
echo [動作] 正在連線 GitHub 雲端為您下載最新「勝一三合一單產生系統」main.py...
echo.

set "RAW_URL=https://raw.githubusercontent.com/shihwei0809/google-agent/main/%%E5%%8B%%9D%%E4%%B8%%80%%E4%%B8%%89%%E5%%90%%88%%E4%%B8%%80%%E5%%96%%AE%%E7%%94%%A2%%E7%%94%%9F%%E7%%B3%%BB%%E7%%B5%%B1/main.py"

if exist "main.py.new" del /f /q "main.py.new" >nul 2>&1

:: 優先嘗試 curl
curl.exe -fsSL "%RAW_URL%" -o "main.py.new" >nul 2>&1
if exist "main.py.new" goto VERIFY_NEW_FILE

:: 備用 PowerShell 下載
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%RAW_URL%', 'main.py.new')" >nul 2>&1
if exist "main.py.new" goto VERIFY_NEW_FILE

echo [警告] 雲端下載失敗，已保留您原本的 main.py 不變。
echo 若需還原舊版，可隨時雙擊「一鍵還原上一版程式.bat」。
pause
goto LAUNCH_APP

:VERIFY_NEW_FILE
set "NEW_SIZE=0"
for %%A in ("main.py.new") do set "NEW_SIZE=%%~zA"
if !NEW_SIZE! LSS 5000 (
    del /f /q "main.py.new" >nul 2>&1
    echo [保護攔截] 下載之檔案大小異常，已自動取消覆蓋並保留原正常版本！
    pause
    goto LAUNCH_APP
)

:: 語法自我檢測
python -m py_compile "main.py.new" >nul 2>&1
if errorlevel 1 (
    del /f /q "main.py.new" >nul 2>&1
    echo [保護攔截] 偵測到雲端新檔語法檢查未通過，已自動攔截並保留原正常版本！
    pause
    goto LAUNCH_APP
)

move /y "main.py.new" "main.py" >nul
echo ============================================================
echo  [成功] 已完成安全驗證並更新至最新 main.py！
echo  *(若使用上有任何問題，雙擊「一鍵還原上一版程式.bat」即可秒退回上一版)*
echo ============================================================
echo.
timeout /t 2 >nul
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 情況 1 的執行流程 (Git pull，具備防呆與自動回滾保護)
:: ------------------------------------------------------------
:GIT_PULL_MODE
echo [狀態] 偵測到本機 Git 版本庫，正在從 GitHub 雲端同步最新版本...
echo.

git stash >nul 2>&1
git pull origin main
if "%ERRORLEVEL%"=="0" goto VERIFY_GIT_MAIN

git fetch origin main >nul 2>&1
git checkout origin/main -- "勝一三合一單產生系統/main.py" >nul 2>&1
if "%ERRORLEVEL%"=="0" goto VERIFY_GIT_MAIN

:: 若 Git 同步異常，改走獨立下載驗證流程
cd /d "%~dp0"
goto CLOUD_DIRECT_DOWNLOAD

:VERIFY_GIT_MAIN
cd /d "%~dp0"
python -m py_compile "main.py" >nul 2>&1
if errorlevel 1 (
    if exist "main_backup_last.py" (
        copy /y "main_backup_last.py" "main.py" >nul
        echo [自動保護] 偵測到更新後語法異常，已自動為您還原回 main_backup_last.py！
        pause
        goto LAUNCH_APP
    )
)

echo.
echo ============================================================
echo  [成功] 雲端更新完成！本機已為最新版本。
echo  *(若使用上有任何問題，雙擊「一鍵還原上一版程式.bat」即可秒退回上一版)*
echo ============================================================
echo.
timeout /t 2 >nul
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 啟動主程式
:: ------------------------------------------------------------
:LAUNCH_APP
cd /d "%~dp0"
if exist "勝一三合一單產生系統.exe" (
    start "" "勝一三合一單產生系統.exe"
) else if exist "dist\勝一三合一單產生系統-免安裝版.exe" (
    start "" "dist\勝一三合一單產生系統-免安裝版.exe"
) else if exist "啟動_勝一三合一單產生器.bat" (
    start "" "啟動_勝一三合一單產生器.bat"
) else (
    start "" python main.py
)
exit
