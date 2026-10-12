@echo off
chcp 950 >nul
title N系小包報表輸出系統 - 一鍵系統更新精靈

echo ============================================================
echo         N系小包報表輸出系統 - 一鍵系統更新精靈
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

set LOCAL_DEV_DIR=D:\GOOGLE ANGET\n系統報表產生
if exist "%LOCAL_DEV_DIR%\main.py" (
    echo ★ 偵測到本機 D 槽存在最新開發程式庫:
    echo   %LOCAL_DEV_DIR%
    echo.
    echo 是否立即從本機 D 槽同步最新 main.py 與檔案至「目前此目錄」？
    set /p SYNC_CHOICE="(Y/N) [預設 Y，按 Enter 直接同步更新]: "
    if "%SYNC_CHOICE%"=="" set SYNC_CHOICE=Y
    if /i "%SYNC_CHOICE%"=="Y" (
        echo 正在同步最新檔案至此目錄...
        copy /y "%LOCAL_DEV_DIR%\main.py" "%~dp0main.py" >nul
        copy /y "%LOCAL_DEV_DIR%\啟動本機視窗版.bat" "%~dp0啟動本機視窗版.bat" >nul
        if exist "%LOCAL_DEV_DIR%\N系料小包-地點代號對照表.xlsx" copy /y "%LOCAL_DEV_DIR%\N系料小包-地點代號對照表.xlsx" "%~dp0N系料小包-地點代號對照表.xlsx" >nul
        echo [成功] 最新程式碼已成功發布更新至此目錄！
        echo.
    )
) else (
    echo [狀態] 目前使用的是共享區最新發布版本。
)

echo 即將為您開啟系統...
timeout /t 2 >nul
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
if errorlevel 1 (
    echo.
    echo [警告] 雲端更新失敗！請檢查網路連線或 Git 狀態。
    echo 將嘗試直接啟動現有程式...
    pause
    goto LAUNCH_APP
)

echo.
echo ============================================================
echo  [成功] 雲端更新完成！本機已為最新版本。
echo ============================================================
echo.

:: 自動巡查各磁碟機尋找 NAS 共享目錄
set NAS_TARGET=
for %%d in (O Z Y X W) do (
    if exist "%%d:\各單位對外\資材部對外\n系統報表產生" (
        set "NAS_TARGET=%%d:\各單位對外\資材部對外\n系統報表產生"
    )
)

if defined NAS_TARGET (
    echo ★ 偵測到公司 NAS 共享區: %NAS_TARGET%
    set /p PUSH_NAS="是否要順便將最新程式同步發布至該 NAS 共享區？(Y/N) [預設 Y]: "
    if "%PUSH_NAS%"=="" set PUSH_NAS=Y
    if /i "%PUSH_NAS%"=="Y" (
        echo 正在發布最新版本至 NAS...
        copy /y "%~dp0main.py" "%NAS_TARGET%\main.py" >nul
        copy /y "%~dp0啟動本機視窗版.bat" "%NAS_TARGET%\啟動本機視窗版.bat" >nul
        copy /y "%~dp0一鍵更新系統程式.bat" "%NAS_TARGET%\一鍵更新系統程式.bat" >nul
        if exist "%~dp0N系料小包-地點代號對照表.xlsx" copy /y "%~dp0N系料小包-地點代號對照表.xlsx" "%NAS_TARGET%\N系料小包-地點代號對照表.xlsx" >nul
        echo [成功] 已成功將最新 main.py 與相關檔案發布至 NAS！
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
if exist "啟動本機視窗版.bat" (
    start 啟動本機視窗版.bat
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