@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set PROJECT_NAME=倉儲儲位 PWA 記錄系統
set DEFAULT_PORT=8010
set START_CMD=python -m uvicorn run_server:app --host 0.0.0.0 --port

set "PKG[0]=fastapi|fastapi>=0.100.0"
set "PKG[1]=uvicorn|uvicorn>=0.22.0"
set "PKG[2]=pydantic|pydantic>=2.0.0"
set "PKG[3]=openpyxl|openpyxl>=3.1.0"
set "PKG[4]=lxml|lxml>=4.9.0"
set "PKG[5]=docx|python-docx>=1.1.0"
set PKG_COUNT=6

set "FOLDER[0]=data"
set "FOLDER[1]=icons"
set "FOLDER[2]=..\backups"
set FOLDER_COUNT=3

set AUTO_BROWSER=YES

title %PROJECT_NAME% - 啟動中...

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  %PROJECT_NAME%
echo  ║  自動環境偵測 + 啟動
echo  ╚══════════════════════════════════════════════════╝
echo.

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
    echo  [!] 找不到 Python！正在開啟下載頁面...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  [2/4] 確認 pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)
echo         pip 正常

echo  [3/4] 套件環境檢查...
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
) else (
    echo         [已有] !IMPORT_NAME!
)
set /a idx+=1
goto :PKG_LOOP
:PKG_DONE

echo  [4/4] 確認資料夾結構...
set /a fidx=0
:FOLDER_LOOP
if %fidx% GEQ %FOLDER_COUNT% goto :FOLDER_DONE
set "FOLDER_PATH=!FOLDER[%fidx%]!"
if not exist "!FOLDER_PATH!" mkdir "!FOLDER_PATH!"
set /a fidx+=1
goto :FOLDER_LOOP
:FOLDER_DONE
if not exist "data\daily_logs.json" echo [] > data\daily_logs.json

set PORT=%DEFAULT_PORT%
netstat -ano | findstr ":%DEFAULT_PORT% " >nul 2>&1
if %errorlevel% == 0 (
    for /L %%p in (8011,1,8050) do (
        if !PORT! == %DEFAULT_PORT% (
            netstat -ano | findstr ":%%p " >nul 2>&1
            if !errorlevel! neq 0 set PORT=%%p
        )
    )
    echo.
    echo  [提醒] 預設 Port %DEFAULT_PORT% 已被佔用，已自動切換至可用 Port: !PORT!
)

set LOCAL_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4.*192\."') do (
    if not defined LOCAL_IP (
        set LOCAL_IP=%%a
        set LOCAL_IP=!LOCAL_IP: =!
    )
)

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  環境檢查完成！正在啟動...                        ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo   本機電腦:  http://localhost:!PORT!
if defined LOCAL_IP echo   手機區網:  http://!LOCAL_IP!:!PORT!
echo.
echo   按 Ctrl+C 停止服務
echo.

if "%AUTO_BROWSER%" == "YES" (
    start /b cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:!PORT!"
)

set PORT=!PORT!
%PYTHON_CMD% -m uvicorn run_server:app --host 0.0.0.0 --port !PORT!

if %errorlevel% neq 0 (
    echo.
    echo  [錯誤] 啟動失敗，請截圖回報管理員。
    pause
)
