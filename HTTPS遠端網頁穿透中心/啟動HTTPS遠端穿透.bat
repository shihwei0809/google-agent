@echo off
:: ============================================================
:: HTTPS 遠端網頁穿透中心 啟動腳本
:: ============================================================
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

:: ============================================================
:: [設定區]
:: ============================================================
set PROJECT_NAME=HTTPS 遠端網頁穿透中心
set DEFAULT_PORT=8800
set START_CMD=python main.py

:: 套件清單格式: import名稱|pip安裝名稱
set "PKG[0]=fastapi|fastapi>=0.100.0"
set "PKG[1]=uvicorn|uvicorn>=0.22.0"
set "PKG[2]=pydantic|pydantic>=2.0.0"
set "PKG[3]=multipart|python-multipart"
set PKG_COUNT=4

:: 必要資料夾
set FOLDER[0]=static
set FOLDER_COUNT=1

:: 啟動後自動開啟瀏覽器？ (YES/NO)
set AUTO_BROWSER=NO
:: ============================================================

title %PROJECT_NAME% - 啟動中...

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  %PROJECT_NAME%
echo  ║  自動環境偵測 + HTTPS 穿透啟動
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
    echo  [!] 找不到 Python！
    echo      需要 Python 3.9 以上。正在開啟下載頁面...
    echo      安裝時請勾選: [x] Add Python to PATH
    echo.
    start https://www.python.org/downloads/
    echo  安裝完成後請重新雙擊此程式。
    pause
    exit /b 1
)

:: ---- STEP 2: 確認 pip ----
echo  [2/4] 確認 pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo         修復 pip 中...
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)
echo         pip 正常

:: ---- STEP 3: 套件自動偵測與安裝 ----
echo  [3/4] 套件環境檢查...
echo.
set /a idx=0
:PKG_LOOP
if %idx% GEQ %PKG_COUNT% goto :PKG_DONE
set "PKG_ENTRY=!PKG[%idx%]!"
for /f "tokens=1,2 delims=|" %%a in ("!PKG_ENTRY!") do (
    set "IMPORT_NAME=%%a"
    set "PIP_NAME=%%b"
)
%PYTHON_CMD% -c "import !IMPORT_NAME!" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] !PIP_NAME! - 安裝中...
    %PYTHON_CMD% -m pip install "!PIP_NAME!" -q
    if !errorlevel! == 0 (
        echo         [完成] !PIP_NAME!
    ) else (
        echo         [失敗] 請手動執行: pip install !PIP_NAME!
    )
) else (
    echo         [OK] !IMPORT_NAME!
)
set /a idx+=1
goto :PKG_LOOP

:PKG_DONE
echo.

:: ---- STEP 4: 啟動伺服器 ----
echo  ==================================================
echo   正在啟動伺服器與 Cloudflare HTTPS 安全穿透...
echo  ==================================================
echo.

%START_CMD%

pause
