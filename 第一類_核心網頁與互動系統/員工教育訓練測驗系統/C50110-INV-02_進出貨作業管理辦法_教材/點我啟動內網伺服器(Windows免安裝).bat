@echo off
chcp 65001 > nul
title 啟動員工教育訓練本機伺服器
echo ============================================================
echo   正在啟動本機內網伺服器，請稍候...
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_intranet.txt"
pause