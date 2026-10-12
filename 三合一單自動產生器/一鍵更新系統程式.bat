@echo off
chcp 950 >nul
title 三合一單自動產生器 - 一鍵系統更新精靈

echo ============================================================
echo         三合一單自動產生器 - 一鍵系統更新精靈
echo ============================================================
echo.

cd /d "%~dp0"

:: 檢查上一層或當前目錄是否為 Git 版本庫
if exist "%~dp0..\.git" goto GIT_MODE
git rev-parse --is-inside-work-tree >nul 2>&1
if "%ERRORLEVEL%"=="0" goto GIT_MODE

:: ------------------------------------------------------------
:: 模式 B：當前執行目錄 (非 Git 本機庫，例如 NAS 共享區或隨身碟)
:: ------------------------------------------------------------
:NAS_MODE
echo [目前執行目錄] %~dp0
echo.

set LOCAL_DEV_DIR=D:\GOOGLE ANGET\三合一單自動產生器
if not exist "%LOCAL_DEV_DIR%\main.py" goto NOT_DEV

echo [偵測] 本機 D 槽存在最新開發程式庫:
echo        %LOCAL_DEV_DIR%
echo.
set SYNC_CHOICE=Y
set /p SYNC_CHOICE=是否立即從本機 D 槽同步最新檔案至此目前目錄 [Y/N, 預設 Y]: 
if /i not "%SYNC_CHOICE%"=="Y" goto SKIP_LOCAL_SYNC

echo.
echo 正在同步最新檔案至此目錄...
copy /y "%LOCAL_DEV_DIR%\main.py" "%~dp0main.py" >nul
copy /y "%LOCAL_DEV_DIR%\啟動_三合一單產生器.bat" "%~dp0啟動_三合一單產生器.bat" >nul
if exist "%LOCAL_DEV_DIR%\地點代號對照表.xlsx" copy /y "%LOCAL_DEV_DIR%\地點代號對照表.xlsx" "%~dp0地點代號對照表.xlsx" >nul
echo [成功] 最新程式碼已成功發布更新至此目錄！
echo.
goto LAUNCH_APP

:NOT_DEV
echo [狀態] 目前使用的是共享區最新發布版本。
echo.
goto LAUNCH_APP

:SKIP_LOCAL_SYNC
echo 略過同步更新。
echo.
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 模式 A：本機 Git 目錄 (D:\GOOGLE ANGET 等)
:: ------------------------------------------------------------
:GIT_MODE
echo [狀態] 偵測到本機 Git 開發儲存庫，正在從 GitHub 雲端拉取最新更新...
echo.

git --version >nul 2>&1
if errorlevel 1 goto MISSING_GIT

cd /d "%~dp0.."
git pull
if errorlevel 1 goto GIT_PULL_FAIL

echo.
echo ============================================================
echo  [成功] 雲端更新完成！本機已為最新版本。
echo ============================================================
echo.

:: 自動巡查各磁碟機尋找 NAS 共享目錄
set NAS_TARGET=
if exist "O:\各單位對外\資材部對外\三合一單自動產生器" set "NAS_TARGET=O:\各單位對外\資材部對外\三合一單自動產生器"
if not defined NAS_TARGET if exist "Z:\各單位對外\資材部對外\三合一單自動產生器" set "NAS_TARGET=Z:\各單位對外\資材部對外\三合一單自動產生器"
if not defined NAS_TARGET if exist "Y:\各單位對外\資材部對外\三合一單自動產生器" set "NAS_TARGET=Y:\各單位對外\資材部對外\三合一單自動產生器"

if not defined NAS_TARGET goto LAUNCH_APP

echo [偵測] 發現公司 NAS 共享區: %NAS_TARGET%
set PUSH_NAS=Y
set /p PUSH_NAS=是否要順便將最新程式同步發布至該 NAS 共享區 [Y/N, 預設 Y]: 
if /i not "%PUSH_NAS%"=="Y" goto LAUNCH_APP

echo.
echo 正在發布最新版本至 NAS...
copy /y "%~dp0main.py" "%NAS_TARGET%\main.py" >nul
copy /y "%~dp0啟動_三合一單產生器.bat" "%NAS_TARGET%\啟動_三合一單產生器.bat" >nul
copy /y "%~dp0一鍵更新系統程式.bat" "%NAS_TARGET%\一鍵更新系統程式.bat" >nul
if exist "%~dp0地點代號對照表.xlsx" copy /y "%~dp0地點代號對照表.xlsx" "%NAS_TARGET%\地點代號對照表.xlsx" >nul
echo [成功] 已成功將最新 main.py 與相關檔案發布至 NAS！
echo.
goto LAUNCH_APP

:GIT_PULL_FAIL
echo.
echo [警告] 雲端更新失敗！請檢查網路連線或 Git 狀態。
echo 將嘗試直接啟動現有程式...
pause
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 啟動主程式
:: ------------------------------------------------------------
:LAUNCH_APP
echo 即將為您開啟系統...
timeout /t 2 >nul
cd /d "%~dp0"
if exist "啟動_三合一單產生器.bat" (
    start "" "%~dp0啟動_三合一單產生器.bat"
) else (
    start python main.py
)
exit

:: ------------------------------------------------------------
:: 缺少 Git 提示
:: ------------------------------------------------------------
:MISSING_GIT
echo [錯誤] 您的電腦尚未安裝 Git 程式！
echo 系統將自動打開網頁，請下載並安裝「Git for Windows」。
echo 安裝時請一直按「Next」到底即可。
echo.
start https://git-scm.com/download/win
pause
exit