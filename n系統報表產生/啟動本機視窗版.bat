@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

title N系小包報表輸出系統

echo.
echo ==============================================
echo   N系小包報表輸出系統 - 啟動本機視窗版
echo ==============================================
echo.

set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=py
)

echo [1/2] 檢查並安裝必要套件...
%PYTHON_CMD% -m pip install openpyxl Pillow qrcode pytesseract -q

echo [2/2] 正在開啟系統視窗，請稍候...
%PYTHON_CMD% main.py

if errorlevel 1 (
    echo.
    echo 啟動發生錯誤！請將上述錯誤訊息截圖。
    pause
)