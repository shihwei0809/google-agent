@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title 三合一單自動產生器 (鴻勝專用版) - 一鍵即時還原上一版程式

echo ============================================================
echo      三合一單自動產生器 (鴻勝專用版) - 一鍵還原上一版程式
echo ============================================================
echo.

cd /d "%~dp0"

if exist "main_backup_last.py" (
    echo [偵測] 已找到更新前自動備份的穩定版本：main_backup_last.py
    for %%A in ("main_backup_last.py") do echo        備份時間：%%~tA  檔案大小：%%~zA bytes
    echo.
    if not exist "backups" mkdir "backups"
    if exist "main.py" (
        copy /y "main.py" "backups\main_before_rollback.py" >nul 2>&1
    )
    copy /y "main_backup_last.py" "main.py" >nul
    echo ============================================================
    echo  [還原成功] 已將 main.py 即時還原回更新前的穩定版本！
    echo ============================================================
    echo.
    timeout /t 2 >nul
    goto LAUNCH_APP
)

:: 若根目錄沒有 main_backup_last.py，自動去 backups 資料夾找最新的一份備份
if exist "backups\main_backup_*.py" (
    set "LATEST_BAK="
    for /f "delims=" %%F in ('dir /b /o-d "backups\main_backup_*.py" 2^>nul') do (
        if not defined LATEST_BAK set "LATEST_BAK=backups\%%F"
    )
    if defined LATEST_BAK (
        echo [偵測] 已從 backups 歷史備份庫找到最近一次備份：!LATEST_BAK!
        copy /y "!LATEST_BAK!" "main.py" >nul
        copy /y "!LATEST_BAK!" "main_backup_last.py" >nul
        echo ============================================================
        echo  [還原成功] 已從 !LATEST_BAK! 還原回 main.py！
        echo ============================================================
        echo.
        timeout /t 2 >nul
        goto LAUNCH_APP
    )
)

echo [提示] 目前尚未找到任何備份檔 (main_backup_last.py 或 backups\*)。
echo        每次您點擊「一鍵更新系統程式.bat」時，系統都會自動建立備份。
echo.
pause
exit

:LAUNCH_APP
cd /d "%~dp0"
if exist "啟動_三合一單產生器.bat" (
    start "" "啟動_三合一單產生器.bat"
) else (
    start "" python main.py
)
exit
