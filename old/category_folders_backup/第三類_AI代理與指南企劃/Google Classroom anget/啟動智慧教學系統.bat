@echo off
chcp 65001 >nul
title 智慧教學系統啟動器
echo ====================================================
echo 🚀 正在背景啟動 TrainBuddy 本地伺服器...
echo ====================================================

:: 殺掉之前可能殘留的 port 3000 進程
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

:: 啟動 node server.js
start /b node server.js

:: 稍等 1.5 秒讓伺服器準備好
timeout /t 2 >nul

echo 🌐 正在瀏覽器中開啟系統...
start http://localhost:3000/index.html

echo.
echo ====================================================
echo 伺服器正在背景運行。
echo 您可以直接關閉此命令提示字元視窗，或按任意鍵關閉。
echo ====================================================
pause >nul
