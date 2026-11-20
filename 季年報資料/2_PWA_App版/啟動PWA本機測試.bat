@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set PROJECT_NAME=鴻勝資材部季年報智慧分析系統 (PWA本機版)
set DEFAULT_PORT=8092

set "PKG[0]=fastapi|fastapi>=0.100.0"
set "PKG[1]=uvicorn|uvicorn>=0.22.0"
set "PKG[2]=openpyxl|openpyxl"
set PKG_COUNT=3

set "FOLDER[0]=data"
set FOLDER_COUNT=1

title %PROJECT_NAME% - 啟動中...
echo.
echo  ============================================================
echo    %PROJECT_NAME%
echo    自動環境偵測 + Port自動切換 + 區網IP顯示
echo  ============================================================
echo.

echo  [1/4] 偵測 Python 環境...
set PYTHON_CMD=
for %%c in (python py python3) do (
    if not defined PYTHON_CMD (
        %%c --version >nul 2>&1
        if !errorlevel! == 0 (
            set PYTHON_CMD=%%c
            for /f "tokens=*" %%v in ('%%c --version 2^>^&1') do echo        找到: %%v
        )
    )
)
if not defined PYTHON_CMD (
    echo  [!] 找不到 Python，正在開啟下載頁面...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  [2/4] 確認 pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)

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
    echo        [安裝] !PIP_NAME!...
    %PYTHON_CMD% -m pip install "!PIP_NAME!" -q
) else (
    echo        [已有] !IMPORT_NAME!
)
set /a idx+=1
goto :PKG_LOOP
:PKG_DONE

echo  [4/4] 確認資料夾結構...
if not exist "data" mkdir "data"

echo.
echo  啟動伺服器中... (關閉此視窗即停止服務)
%PYTHON_CMD% run_server.py
pause
