@echo off
:: ============================================================
:: 通用專案啟動 BAT 模板 (AI 圖片/PDF 雙重 OCR 轉 Excel 系統)
:: ============================================================
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set PYTHONWARNINGS=ignore

:: ============================================================
:: [設定區]
:: ============================================================
set PROJECT_NAME=AI 圖片/PDF 雙重 OCR 轉 Excel 系統
set DEFAULT_PORT=8000
set START_CMD=python ocr_web_app.py

:: 套件清單格式: import名稱|pip安裝名稱
set "PKG[0]=fastapi|fastapi>=0.100.0"
set "PKG[1]=uvicorn|uvicorn>=0.22.0"
set "PKG[2]=multipart|python-multipart"
set "PKG[3]=openpyxl|openpyxl"
set "PKG[4]=PIL|Pillow"
set "PKG[5]=fitz|pymupdf"
set "PKG[6]=easyocr|easyocr"
set "PKG[7]=google.genai|google-genai"
set PKG_COUNT=8

:: 必要資料夾
set "FOLDER[0]=outputs"
set FOLDER_COUNT=1

:: 啟動後自動開啟瀏覽器？ (YES/NO)
set AUTO_BROWSER=YES
:: ============================================================

title %PROJECT_NAME% - 啟動中...

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  %PROJECT_NAME%
echo  ║  自動環境偵測 + 依賴安裝 + 啟動
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
echo  [3/4] 套件環境檢查（若人員電腦缺少套件會自動下載安裝）...
echo.
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
    echo         [缺少] !PIP_NAME! - 自動下載安裝中，請稍候...
    %PYTHON_CMD% -m pip install "!PIP_NAME!" -q
    if !errorlevel! == 0 (
        echo         [完成] !PIP_NAME! 安裝成功！
    ) else (
        echo         [失敗] !PIP_NAME! 安裝失敗，請確認網路連線
    )
) else (
    echo         [已有] !IMPORT_NAME!
)
set /a idx+=1
goto :PKG_LOOP
:PKG_DONE

:: ---- STEP 4: 建立必要資料夾 ----
echo.
echo  [4/4] 確認資料夾結構...
set /a fidx=0
:FOLDER_LOOP
if %fidx% GEQ %FOLDER_COUNT% goto :FOLDER_DONE
set "FOLDER_PATH=!FOLDER[%fidx%]!"
if not exist "!FOLDER_PATH!" (
    mkdir "!FOLDER_PATH!"
    echo         建立: !FOLDER_PATH!
)
set /a fidx+=1
goto :FOLDER_LOOP
:FOLDER_DONE
echo         資料夾正常

:: ---- 找可用 Port ----
set PORT=%DEFAULT_PORT%
for /L %%p in (%DEFAULT_PORT%,1,8050) do (
    if !PORT! == %DEFAULT_PORT% (
        netstat -ano | findstr ":%%p " >nul 2>&1
        if !errorlevel! neq 0 set PORT=%%p
    )
)
if not !PORT! == %DEFAULT_PORT% (
    echo.
    echo  [提醒] Port %DEFAULT_PORT% 已被佔用，改用 Port !PORT!
)

:: ---- 取得本機 IP ----
set LOCAL_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4.*192\."') do (
    if not defined LOCAL_IP (
        set LOCAL_IP=%%a
        set LOCAL_IP=!LOCAL_IP: =!
    )
)

:: ---- 啟動 ----
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  環境檢查完成！正在啟動伺服器...                ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo   本機:  http://localhost:!PORT!
if defined LOCAL_IP echo   區網:  http://!LOCAL_IP!:!PORT!
echo.
echo   按 Ctrl+C 停止服務
echo.

if "%AUTO_BROWSER%" == "YES" (
    start /b cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:!PORT!"
)

%START_CMD% !PORT!

if %errorlevel% neq 0 (
    echo.
    echo  [錯誤] 啟動失敗，請截圖以上訊息回報。
    echo.
    pause
)
