@echo off
:: ============================================================
:: AI 影音自動剪輯工作站 專屬啟動腳本
:: ============================================================
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set PROJECT_NAME=AI 影音自動剪輯工作站
set DEFAULT_PORT=8050
set START_CMD=python -m uvicorn main:app --host 0.0.0.0 --port

:: 依據專案掃描填入套件
set PKG[0]=fastapi|fastapi>=0.100.0
set PKG[1]=uvicorn|uvicorn>=0.22.0
set PKG[2]=multipart|python-multipart
set PKG[3]=jinja2|jinja2
set PKG[4]=edge_tts|edge-tts>=7.3.0
set PKG[5]=PIL|pillow
set PKG_COUNT=6

set FOLDER[0]=uploads
set FOLDER[1]=outputs
set FOLDER[2]=templates
set FOLDER[3]=static
set FOLDER_COUNT=4

set AUTO_BROWSER=YES

title %PROJECT_NAME% - 啟動中...

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  %PROJECT_NAME%
echo  ║  自動環境偵測 + 啟動
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ---- STEP 1: 偵測 Python ----
echo  [1/4] 偵測 Python 環境...
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
    echo  [錯誤] 找不到 Python！
    echo  請先安裝 Python (建議 3.10 以上，並勾選 Add to PATH)
    pause
    exit /b 1
)

:: ---- STEP 2: 檢查 pip ----
echo  [2/4] 檢查 pip 與必要套件...
%PYTHON_CMD% -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo         pip 異常，嘗試修復...
    %PYTHON_CMD% -m ensurepip --default-pip >nul 2>&1
)

set MISSING_COUNT=0
set MAX_IDX=%PKG_COUNT%
set /a MAX_IDX-=1

for /l %%i in (0,1,%MAX_IDX%) do (
    for /f "tokens=1,2 delims=|" %%a in ("!PKG[%%i]!") do (
        set MOD=%%a
        set PIP_PKG=%%b
        %PYTHON_CMD% -c "import !MOD!" >nul 2>&1
        if !errorlevel! neq 0 (
            echo         缺少套件: !PIP_PKG!，正在自動安裝...
            %PYTHON_CMD% -m pip install !PIP_PKG!
            set /a MISSING_COUNT+=1
        ) else (
            echo         [OK] !MOD!
        )
    )
)

:: ---- STEP 3: 建立必要資料夾 ----
echo  [3/4] 檢查專案資料夾結構...
set F_MAX=%FOLDER_COUNT%
set /a F_MAX-=1
for /l %%i in (0,1,%F_MAX%) do (
    set TARGET_DIR=!FOLDER[%%i]!
    if not exist "!TARGET_DIR!" (
        echo         建立: !TARGET_DIR!\
        mkdir "!TARGET_DIR!" >nul 2>&1
    )
)
echo         資料夾結構就緒

:: ---- STEP 4: Port 偵測與自動切換 ----
echo  [4/4] 偵測可用 Port...
set TARGET_PORT=%DEFAULT_PORT%

:CHECK_PORT
netstat -ano | findstr /r /c:":%TARGET_PORT% *LISTENING" >nul 2>&1
if !errorlevel! == 0 (
    echo         Port %TARGET_PORT% 已被佔用
    set /a TARGET_PORT+=1
    echo         嘗試切換至 Port !TARGET_PORT!...
    goto CHECK_PORT
)
echo         使用 Port: %TARGET_PORT%

:: 抓取本機區網 IP
set LOCAL_IP=127.0.0.1
for /f "tokens=4" %%a in ('route print 0.0.0.0 2^>nul ^| findstr "0.0.0.0 *0.0.0.0"') do (
    if "!LOCAL_IP!" == "127.0.0.1" (
        ping -n 1 -w 100 %%a >nul 2>&1
        if !errorlevel! == 0 set LOCAL_IP=%%a
    )
)

:: ---- 啟動伺服器 ----
echo.
echo  ══════════════════════════════════════════════════
echo   服務已就緒！
echo   本機網址:   http://localhost:%TARGET_PORT%
echo   區網網址:   http://!LOCAL_IP!:%TARGET_PORT%
echo  ══════════════════════════════════════════════════
echo.

if "%AUTO_BROWSER%" == "YES" (
    start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:%TARGET_PORT%"
)

title %PROJECT_NAME% (Port: %TARGET_PORT%)
%START_CMD% %TARGET_PORT%

if !errorlevel! neq 0 (
    echo.
    echo  [提示] 服務已停止
    pause
)
