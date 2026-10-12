@echo off
chcp 950 >nul
title N系小包報表輸出系統 - 一鍵系統更新精靈

echo ============================================================
echo         N系小包報表輸出系統 - 一鍵系統更新精靈
echo ============================================================
echo.

cd /d "%~dp0"

:: ------------------------------------------------------------
:: 1. 判斷是否為本機 Git 開發儲存庫 (開發者模式)
:: ------------------------------------------------------------
if exist "%~dp0..\.git" goto GIT_DEV_MODE
git rev-parse --is-inside-work-tree >nul 2>&1
if "%ERRORLEVEL%"=="0" goto GIT_DEV_MODE

:: ------------------------------------------------------------
:: 2. 非 Git 目錄：判斷是在 NAS 上，還是在同仁本機電腦 (C 槽/D 槽/桌面等)
:: ------------------------------------------------------------
:LOCAL_OR_NAS_MODE

:: 尋找公司 NAS 共享區來源路徑 (依序檢查 O: 槽、Z 槽與 UNC 網路路徑)
set NAS_SRC=
if exist "O:\各單位對外\資材部對外\n系統報表產生\main.py" set "NAS_SRC=O:\各單位對外\資材部對外\n系統報表產生"
if not defined NAS_SRC if exist "Z:\各單位對外\資材部對外\n系統報表產生\main.py" set "NAS_SRC=Z:\各單位對外\資材部對外\n系統報表產生"
if not defined NAS_SRC if exist "\\192.168.3.224\eshine\各單位對外\資材部對外\n系統報表產生\main.py" set "NAS_SRC=\\192.168.3.224\eshine\各單位對外\資材部對外\n系統報表產生"

:: 檢查「當前執行目錄 %~dp0」是否就是 NAS 本身
set CURRENT_DIR=%~dp0
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

if /i "%CURRENT_DIR%"=="O:\各單位對外\資材部對外\n系統報表產生" goto RUNNING_ON_NAS
if /i "%CURRENT_DIR%"=="\\192.168.3.224\eshine\各單位對外\資材部對外\n系統報表產生" goto RUNNING_ON_NAS

:: 若執行電腦剛好有 D 槽開發庫 (開發者在 NAS 目錄被執行的情況)
if exist "D:\GOOGLE ANGET\n系統報表產生\main.py" goto DEV_ON_NAS

:: ------------------------------------------------------------
:: 情況 A：同仁在自己本機電腦 (C 槽、D 槽、桌面等任意位置)
:: ------------------------------------------------------------
:COLLEAGUE_LOCAL_UPDATE
echo [目前位置] %~dp0
echo.
if not defined NAS_SRC goto NAS_NOT_FOUND

echo [偵測] 成功連線公司 NAS 最新發布區:
echo        %NAS_SRC%
echo.
echo 正在為您從 NAS 同步最新程式至目前本機目錄...
copy /y "%NAS_SRC%\main.py" "%~dp0main.py" >nul
copy /y "%NAS_SRC%\啟動本機視窗版.bat" "%~dp0啟動本機視窗版.bat" >nul
copy /y "%NAS_SRC%\一鍵更新系統程式.bat" "%~dp0一鍵更新系統程式.bat" >nul
if exist "%NAS_SRC%\N系料小包-地點代號對照表.xlsx" copy /y "%NAS_SRC%\N系料小包-地點代號對照表.xlsx" "%~dp0N系料小包-地點代號對照表.xlsx" >nul
echo [成功] 本機程式已更新至最新版本！
echo.
goto LAUNCH_APP

:NAS_NOT_FOUND
echo [提示] 目前無法連線至公司 NAS (請確認是否在廠內網路)。
echo 將直接以本機現有版本為您啟動...
echo.
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 情況 B：開發者在 NAS 上點開執行 (提供一鍵從 D 槽發布至 NAS)
:: ------------------------------------------------------------
:DEV_ON_NAS
echo [目前位置] %~dp0
echo ★ 偵測到本機存在開發最新庫: D:\GOOGLE ANGET\n系統報表產生
set SYNC_D2NAS=Y
set /p SYNC_D2NAS=是否立即從本機 D 槽同步最新檔案覆蓋至此 NAS 目錄 [Y/N, 預設 Y]: 
if /i not "%SYNC_D2NAS%"=="Y" goto LAUNCH_APP

echo 正在將最新檔案發布至此 NAS 目錄...
copy /y "D:\GOOGLE ANGET\n系統報表產生\main.py" "%~dp0main.py" >nul
copy /y "D:\GOOGLE ANGET\n系統報表產生\啟動本機視窗版.bat" "%~dp0啟動本機視窗版.bat" >nul
if exist "D:\GOOGLE ANGET\n系統報表產生\N系料小包-地點代號對照表.xlsx" copy /y "D:\GOOGLE ANGET\n系統報表產生\N系料小包-地點代號對照表.xlsx" "%~dp0N系料小包-地點代號對照表.xlsx" >nul
echo [成功] 已成功將最新檔案同步至此 NAS 目錄！
echo.
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 情況 C：同仁直接在 NAS 共享區上開啟執行 (免安裝模式)
:: ------------------------------------------------------------
:RUNNING_ON_NAS
echo [目前位置] %~dp0
echo [狀態] 目前直接於 NAS 共享區執行，此目錄已是最新版本！
echo.
goto LAUNCH_APP

:: ------------------------------------------------------------
:: 情況 D：開發者在 D 槽本機執行 (Git 模式)
:: ------------------------------------------------------------
:GIT_DEV_MODE
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

set NAS_TARGET=
if exist "O:\各單位對外\資材部對外\n系統報表產生" set "NAS_TARGET=O:\各單位對外\資材部對外\n系統報表產生"
if not defined NAS_TARGET if exist "Z:\各單位對外\資材部對外\n系統報表產生" set "NAS_TARGET=Z:\各單位對外\資材部對外\n系統報表產生"
if not defined NAS_TARGET if exist "\\192.168.3.224\eshine\各單位對外\資材部對外\n系統報表產生" set "NAS_TARGET=\\192.168.3.224\eshine\各單位對外\資材部對外\n系統報表產生"

if not defined NAS_TARGET goto LAUNCH_APP

echo [偵測] 發現公司 NAS 共享區: %NAS_TARGET%
set PUSH_NAS=Y
set /p PUSH_NAS=是否要順便將最新程式同步發布至該 NAS 共享區 [Y/N, 預設 Y]: 
if /i not "%PUSH_NAS%"=="Y" goto LAUNCH_APP

echo.
echo 正在發布最新版本至 NAS...
copy /y "%~dp0main.py" "%NAS_TARGET%\main.py" >nul
copy /y "%~dp0啟動本機視窗版.bat" "%NAS_TARGET%\啟動本機視窗版.bat" >nul
copy /y "%~dp0一鍵更新系統程式.bat" "%NAS_TARGET%\一鍵更新系統程式.bat" >nul
if exist "%~dp0N系料小包-地點代號對照表.xlsx" copy /y "%~dp0N系料小包-地點代號對照表.xlsx" "%NAS_TARGET%\N系料小包-地點代號對照表.xlsx" >nul
echo [成功] 已成功將最新檔案同步發布至 NAS！
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
if exist "啟動本機視窗版.bat" (
    start "" "%~dp0啟動本機視窗版.bat"
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