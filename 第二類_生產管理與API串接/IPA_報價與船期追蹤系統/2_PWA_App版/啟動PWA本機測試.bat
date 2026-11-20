@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul 2>&1

:: ============================================================
:: [設定區] IPA (異丙醇) 報價與出貨單船期自動追蹤系統
:: ============================================================
set PROJECT_NAME=IPA (異丙醇) 報價與出貨單船期自動追蹤系統
set DEFAULT_PORT=8088
set START_CMD=python run_server.py

set "PKG[0]=requests|requests"
set "PKG[1]=PIL|pillow"
set "PKG[2]=docx|python-docx"
set PKG_COUNT=3

set "FOLDER[0]=data"
set "FOLDER[1]=icons"
set FOLDER_COUNT=2

set AUTO_BROWSER=YES
:: ============================================================

title %PROJECT_NAME% - 啟動中...

echo.
echo  ======================================================
echo   %PROJECT_NAME%
echo   自動環境偵測 + 啟動本機看板與爬蟲服務
echo  ======================================================
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
    echo  [!] 找不到 Python！正在開啟下載頁面...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ---- STEP 2: 確認 pip ----
echo  [2/4] 確認 pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)
echo         pip 正常

:: ---- STEP 3: 套件自動偵測與安裝 ----
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

:: ---- STEP 4: 建立必要資料夾 ----
echo  [4/4] 確認資料夾結構...
set /a fidx=0
:FOLDER_LOOP
if %fidx% GEQ %FOLDER_COUNT% goto :FOLDER_DONE
set "FOLDER_PATH=!FOLDER[%fidx%]!"
if not exist "!FOLDER_PATH!" mkdir "!FOLDER_PATH!"
set /a fidx+=1
goto :FOLDER_LOOP
:FOLDER_DONE

:: ---- 找可用 Port ----
set PORT=%DEFAULT_PORT%
for /L %%p in (%DEFAULT_PORT%,1,8130) do (
    if !PORT! == %DEFAULT_PORT% (
        netstat -ano | findstr ":%%p " >nul 2>&1
        if !errorlevel! neq 0 set PORT=%%p
    )
)
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
echo  ======================================================
echo   環境檢查完成！正在啟動伺服器...
echo   本機網址:  http://localhost:!PORT!
if defined LOCAL_IP echo   區網網址:  http://!LOCAL_IP!:!PORT!
echo  ======================================================
echo.

if "%AUTO_BROWSER%" == "YES" (
    start /b cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:!PORT!"
)

%PYTHON_CMD% run_server.py !PORT!

if %errorlevel% neq 0 (
    echo.
    echo  [錯誤] 啟動失敗，請檢查上方錯誤訊息。
    pause
)
