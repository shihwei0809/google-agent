@echo off
:: ============================================================
:: 通用專案啟動 BAT 模板 (bat_launcher_template.bat)
:: 複製到新專案後，只需修改下方 [設定區] 的內容
:: ============================================================
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

:: ============================================================
:: [設定區] 每個專案只需改這裡
:: ============================================================
set PROJECT_NAME=AI 面試語音分析系統
set DEFAULT_PORT=8000
set START_CMD=python -m uvicorn main:app --host 0.0.0.0 --port

:: 套件清單格式: import名稱|pip安裝名稱
:: import名稱用於 python -c "import XXX" 測試
:: pip安裝名稱用於 pip install XXX
set PKG[0]=fastapi|fastapi>=0.100.0
set PKG[1]=uvicorn|uvicorn>=0.22.0
set PKG[2]=google.genai|google-genai
set PKG[3]=pydantic|pydantic>=2.0.0
set PKG[4]=multipart|python-multipart
set PKG[5]=openpyxl|openpyxl
set PKG[6]=docx|python-docx
:: set PKG[7]=requests|requests         ← 需要爬蟲時取消註解
:: set PKG[8]=bs4|beautifulsoup4        ← 需要爬蟲時取消註解
set PKG_COUNT=7

:: 必要資料夾 (空字串表示不需要)
set FOLDER[0]=data
set FOLDER[1]=data\audios
set FOLDER[2]=static
set FOLDER_COUNT=3

:: 啟動後自動開啟瀏覽器？ (YES/NO)
set AUTO_BROWSER=YES
:: ============================================================

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
set PKG_ENTRY=!PKG[%idx%]!
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
        echo         [失敗] !PIP_NAME! 安裝失敗，請截圖回報管理員
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
set FOLDER_PATH=!FOLDER[%fidx%]!
if not exist "!FOLDER_PATH!" (
    mkdir "!FOLDER_PATH!"
    echo         建立: !FOLDER_PATH!
)
set /a fidx+=1
goto :FOLDER_LOOP
:FOLDER_DONE
if not exist "data\db.json" echo [] > data\db.json
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
echo  ║  環境檢查完成！正在啟動...                        ║
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
    echo  [錯誤] 啟動失敗，請截圖以上訊息回報管理員。
    echo.
    pause
)
