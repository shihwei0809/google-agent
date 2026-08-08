@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title AI 面試語音分析系統 - 啟動中...

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║      AI 面試語音分析系統  ^|  自動環境偵測啟動      ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ============================================================
:: STEP 1 - 偵測 Python
:: ============================================================
echo  [1/4] 偵測 Python 環境...
set PYTHON_CMD=

python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=python
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo         找到: %%v
    goto :CHECK_PIP
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=py
    for /f "tokens=*" %%v in ('py --version 2^>^&1') do echo         找到: %%v
    goto :CHECK_PIP
)

:: Python 未安裝 → 自動引導下載
echo.
echo  [!] 未偵測到 Python！
echo.
echo  系統需要 Python 3.9 以上才能運行。
echo  正在為您開啟 Python 官方下載頁面...
echo.
echo  安裝時請務必勾選: [x] Add Python to PATH
echo.
start https://www.python.org/downloads/
echo  下載安裝 Python 後，請重新雙擊此 .bat 啟動。
echo.
pause
exit /b 1

:CHECK_PIP
:: ============================================================
:: STEP 2 - 確認 pip
:: ============================================================
echo  [2/4] 確認 pip 套件管理器...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo         pip 未就緒，正在修復...
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)
echo         pip 正常

:: ============================================================
:: STEP 3 - 逐一檢查必要套件，缺少則自動安裝
:: ============================================================
echo  [3/4] 檢查並安裝必要套件...
echo.

set INSTALL_LIST=

:: fastapi
%PYTHON_CMD% -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] fastapi - 安裝中...
    %PYTHON_CMD% -m pip install "fastapi>=0.100.0" -q
    echo         [完成] fastapi
) else ( echo         [已有] fastapi )

:: uvicorn
%PYTHON_CMD% -c "import uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] uvicorn - 安裝中...
    %PYTHON_CMD% -m pip install "uvicorn>=0.22.0" -q
    echo         [完成] uvicorn
) else ( echo         [已有] uvicorn )

:: google-genai
%PYTHON_CMD% -c "import google.genai" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] google-genai - 安裝中...
    %PYTHON_CMD% -m pip install google-genai -q
    echo         [完成] google-genai
) else ( echo         [已有] google-genai )

:: pydantic
%PYTHON_CMD% -c "import pydantic" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] pydantic - 安裝中...
    %PYTHON_CMD% -m pip install "pydantic>=2.0.0" -q
    echo         [完成] pydantic
) else ( echo         [已有] pydantic )

:: python-multipart
%PYTHON_CMD% -c "import multipart" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] python-multipart - 安裝中...
    %PYTHON_CMD% -m pip install python-multipart -q
    echo         [完成] python-multipart
) else ( echo         [已有] python-multipart )

:: openpyxl
%PYTHON_CMD% -c "import openpyxl" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] openpyxl - 安裝中...
    %PYTHON_CMD% -m pip install openpyxl -q
    echo         [完成] openpyxl
) else ( echo         [已有] openpyxl )

:: python-docx
%PYTHON_CMD% -c "import docx" >nul 2>&1
if %errorlevel% neq 0 (
    echo         [缺少] python-docx - 安裝中...
    %PYTHON_CMD% -m pip install python-docx -q
    echo         [完成] python-docx
) else ( echo         [已有] python-docx )

:: ============================================================
:: STEP 4 - 確認資料夾結構
:: ============================================================
echo.
echo  [4/4] 確認資料夾結構...
if not exist "data" mkdir data
if not exist "data\audios" mkdir data\audios
if not exist "static" mkdir static
if not exist "data\db.json" echo [] > data\db.json
echo         資料夾正常

:: ============================================================
:: 自動找可用 Port (避免衝突)
:: ============================================================
set PORT=8000
for /L %%p in (8000,1,8050) do (
    if !PORT! == 8000 (
        netstat -ano | findstr ":%%p " >nul 2>&1
        if !errorlevel! neq 0 (
            set PORT=%%p
        )
    )
)

:: 取得本機 IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4.*192\."') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP: =!
)

:: ============================================================
:: 啟動服務
:: ============================================================
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  環境檢查完成！正在啟動服務...                    ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo   本機存取:  http://localhost:%PORT%
if defined LOCAL_IP echo   區網存取:  http://%LOCAL_IP%:%PORT%  ^(可提供給同事使用^)
echo.
echo   按 Ctrl+C 可停止服務
echo.

:: 延遲 2 秒後自動開啟瀏覽器
start /b cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:%PORT%"

%PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port %PORT%

if %errorlevel% neq 0 (
    echo.
    echo  [錯誤] 服務啟動失敗，請截圖以上錯誤訊息回報管理員。
    echo.
    pause
)
