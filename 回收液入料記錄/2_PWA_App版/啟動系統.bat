@echo off
chcp 65001 >nul
echo 正在啟動 回收液入料記錄系統...
cd /d "%~dp0"

echo 正在檢查 Python 環境與套件...
python -m pip install -r requirements.txt

echo 啟動系統伺服器...
python main.py
pause
