@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set PROJECT_NAME=Shinyi-3in1-Generator
set START_CMD=python main.py

set "PKG[0]=openpyxl|openpyxl"
set "PKG[1]=qrcode|qrcode"
set "PKG[2]=PIL|Pillow"
set "PKG[3]=pytesseract|pytesseract"
set "PKG[4]=docx|python-docx"
set "PKG[5]=win32com.client|pywin32"
set PKG_COUNT=6

title %PROJECT_NAME%

echo.
echo  ======================================================
echo    ?????????? (Shinyi TSMC 3-in-1 System)
echo    Environment Check and Start
echo  ======================================================
echo.

echo  [1/3] Checking Python...
set PYTHON_CMD=
for %%c in (python py python3) do (
    if not defined PYTHON_CMD (
        %%c --version >nul 2>&1
        if !errorlevel! == 0 (
            set PYTHON_CMD=%%c
            for /f "tokens=*" %%v in ('%%c --version 2^>^&1') do echo         Found: %%v
        )
    )
)

if not defined PYTHON_CMD (
    echo.
    echo  [!] Python not found!
    echo      Python 3.9+ is required. Opening download page...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  [2/3] Checking dependencies...
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
    echo         [Missing] !PIP_NAME! - Installing...
    %PYTHON_CMD% -m pip install "!PIP_NAME!" -q
) else (
    echo         [OK] !IMPORT_NAME!
)
set /a idx+=1
goto :PKG_LOOP
:PKG_DONE

echo.
echo  [3/3] Starting Application...
echo.

%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
    echo.
    echo  [Error] Application exited unexpectedly.
    pause
)