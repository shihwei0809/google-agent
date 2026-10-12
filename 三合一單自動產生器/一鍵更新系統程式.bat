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
:: 模式 B：非 Git 目錄 (例如 NAS O: 槽或一般網路共享目錄)
:: ------------------------------------------------------------
:NAS_MODE
echo [狀態] 偵測到目前位於「NAS 網路共享區」或一般資料夾 (非 Git 本機庫)。
echo        路徑: %~dp0
echo.
echo 說明:
echo  1. 此共享目錄無 Git 版本控制，無法直接執行雲端 git pull。
echo  2. 若要更新此處，請於開發本機 (D 槽) 更新後，將檔案複製發布至此處。
echo.

set LOCAL_DEV_DIR=D:\GOOGLE ANGET\三合一單自動產生器
if exist "%LOCAL_DEV_DIR%\main.py" (
    echo ★ 偵測到本機 D 槽存在開發最新庫:
    echo   %LOCAL_DEV_DIR%
    echo.
    set /p SYNC_CHOICE="是否立即從本機 D 槽同步最新 main.py 與檔案至此 NAS 目錄？(Y/N) [預設 N]: "
    if /i "%SYNC_CHOICE%"=="Y" (
        echo 正在同步檔案中...
        copy /y "%LOCAL_DEV_DIR%\main.py" "%~dp0main.py" >nul
        if exist "%LOCAL_DEV_DIR%\地點代號對照表.xlsx" copy /y "%LOCAL_DEV_DIR%\地點代號對照表.xlsx" "%~dp0地點代號對照表.xlsx" >nul
        echo [成功] 最新程式已成功同步至此共享目錄！
        echo.
    )
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

set NAS_DIR=O:\各單位對外\資材部對外\三合一單自動產生器
if exist "%NAS_DIR%" (
    echo ★ 偵測到公司 NAS (O 槽) 連線正常！
    set /p PUSH_NAS="是否要順便將最新程式同步發布至 NAS 共享區？(Y/N) [預設 Y]: "
    if "%PUSH_NAS%"=="" set PUSH_NAS=Y
    if /i "%PUSH_NAS%"=="Y" (
        echo 正在發布最新版本至 NAS...
        copy /y "%~dp0main.py" "%NAS_DIR%\main.py" >nul
        copy /y "%~dp0一鍵更新系統程式.bat" "%NAS_DIR%\一鍵更新系統程式.bat" >nul
        echo [成功] 已成功將最新 main.py 發布至 NAS 共享區！
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
