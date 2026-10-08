@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

title N系小包報表輸出系統

echo.
echo ==============================================
echo   N系小包報表輸出系統 - 環境檢查與啟動
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
start "" %PYTHON_CMD%w main.py

exit