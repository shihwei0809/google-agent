@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

title 企業活動簽到系統 - PWA 本機測試伺服器

set PYTHON_CMD=
for %%c in (python py python3) do (
    if not defined PYTHON_CMD (
        %%c --version >nul 2>&1
        if !errorlevel! == 0 set PYTHON_CMD=%%c
    )
)

if not defined PYTHON_CMD (
    echo [!] 找不到 Python，正在開啟下載頁面...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

%PYTHON_CMD% run_server.py 8080
pause
