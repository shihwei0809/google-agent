@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set PROJECT_NAME=勝一 QR Code 五掃核對系統
set DEFAULT_PORT=8002
set START_CMD=python main.py

set PKG[0]=fastapi|fastapi>=0.100.0
set PKG[1]=uvicorn|uvicorn>=0.22.0
set PKG_COUNT=2

title %PROJECT_NAME% - 啟動中...

echo.
echo  ======================================================
echo    %PROJECT_NAME%
echo    自動環境偵測 + 啟動
echo  ======================================================
echo.

:: ---- STEP 1: 偵測 Python ----
set PYTHON_CMD=
for %%c in (python py python3) do (
    if not defined PYTHON_CMD (
        %%c --version >nul 2>&1
        if !errorlevel! == 0 set PYTHON_CMD=%%c
    )
)

if not defined PYTHON_CMD (
    echo [!] 找不到 Python！請手動安裝。
pause
    exit /b 1
)

:: ---- STEP 2: 套件自動偵測與安裝 ----
set /a idx=0
:PKG_LOOP
if !idx! GEQ %PKG_COUNT% goto :PKG_DONE
set PKG_ENTRY=!PKG[%idx%]!
for /f "tokens=1,2 delims=|" %%a in ("!PKG_ENTRY!") do (
    !PYTHON_CMD! -c "import %%a" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [安裝] 缺少 %%b，正在自動安裝...
        !PYTHON_CMD! -m pip install "%%b" -q
    )
)
set /a idx+=1
goto :PKG_LOOP
:PKG_DONE

:: ---- 啟動 ----
echo [啟動] 正在啟動伺服器...
%START_CMD%

pause