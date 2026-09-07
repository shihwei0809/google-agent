@echo off
chcp 65001 >nul
echo ===================================================
echo   🚀 正在啟動 勝一化工 - 產銷計畫 PWA 獨立 App 伺服器...
echo ===================================================
cd /d "%~dp02_PWA_App版"
python run_server.py
pause
