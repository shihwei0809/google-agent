@echo off
chcp 65001 >nul
echo =========================================
echo      啟動 PWA 雙軌系統本機測試伺服器
echo =========================================
python run_server.py
pause
