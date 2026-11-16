@echo off
:: ============================================================
:: Blender 3D AI建模與白模運鏡系統 - 一鍵啟動 (自動環境偵測)
:: ============================================================
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set PROJECT_NAME=Blender 3D AI建模與白模運鏡系統
set DEFAULT_PORT=8088

set "PKG[0]=docx|python-docx"
set "PKG[1]=PIL|pillow"
set PKG_COUNT=2

set AUTO_BROWSER=YES

title %PROJECT_NAME% - 啟動中...

echo.
echo  ====================================================
echo   %PROJECT_NAME%
echo   自動環境偵測 + Port 備援切換 + 啟動
echo  ====================================================
echo.

:: ---- STEP 1: 偵測 Python ----
echo  [1/3] 偵測 Python 環境...
set PYTHON_CMD=
for %%c in (python py python3) do (
    if not defined PYTHON_CMD (
        %%c --version >nul 2>&1
        if !errorlevel! == 0 (
            set PYTHON_CMD=%%c
            for /f "tokens=*" %%v in ('%%c --version 2^>^&1') do echo         找到: %%v
        )
    )
)

if not defined PYTHON_CMD (
    echo.
    echo  [!] 找不到 Python！需要 Python 3.9 以上，正在開啟下載頁面...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ---- STEP 2: 確認 pip ----
echo  [2/3] 確認 pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo         修復 pip 中...
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)
echo         pip 正常

:: ---- STEP 3: 套件自動偵測與安裝 ----
echo  [3/3] 套件環境檢查...
set /a idx=0
:PKG_LOOP
if %idx% GEQ %PKG_COUNT% goto :PKG_DONE
set "PKG_ENTRY=!PKG[%idx%]!"
for /f "tokens=1,2 delims=|" %%a in ("!PKG_ENTRY!") do (
    set IMPORT_NAME=%%a
    set PIP_NAME=%%b
)
%PYTHON_CMD% -c "import !IMPORT_NAME!" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] !PIP_NAME! - 安裝中...
    %PYTHON_CMD% -m pip install "!PIP_NAME!" -q
    if !errorlevel! == 0 (
        echo         [完成] !PIP_NAME!
    ) else (
        echo         [失敗] !PIP_NAME! 安裝失敗
    )
) else (
    echo         [已有] !IMPORT_NAME!
)
set /a idx+=1
goto :PKG_LOOP
:PKG_DONE

:: ---- 找可用 Port ----
set PORT=%DEFAULT_PORT%
set FOUND_PORT=
for /L %%p in (%DEFAULT_PORT%,1,8120) do (
    if not defined FOUND_PORT (
        netstat -ano | findstr ":%%p " >nul 2>&1
        if !errorlevel! neq 0 set FOUND_PORT=%%p
    )
)
if defined FOUND_PORT set PORT=%FOUND_PORT%
if not !PORT! == %DEFAULT_PORT% (
    echo.
    echo  [提醒] 預設 Port %DEFAULT_PORT% 已被佔用，自動切換至可用 Port: !PORT!
)

:: ---- 取得本機 IP ----
set LOCAL_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4.*192\."') do (
    if not defined LOCAL_IP (
        set LOCAL_IP=%%a
        set LOCAL_IP=!LOCAL_IP: =!
    )
)

echo.
echo   本機儲位看板: http://localhost:!PORT!/index.html
echo   FPV 白模工作室: http://localhost:!PORT!/fpv_studio.html
if defined LOCAL_IP echo   區網手機預覽: http://!LOCAL_IP!:!PORT!/index.html
echo.
echo   按 Ctrl+C 停止服務
echo.

if "%AUTO_BROWSER%" == "YES" (
    start /b cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:!PORT!/index.html"
)

%PYTHON_CMD% run_server.py --no-browser !PORT!

if %errorlevel% neq 0 (
    echo.
    echo  [錯誤] 啟動失敗，請截圖以上訊息。
    pause
)
