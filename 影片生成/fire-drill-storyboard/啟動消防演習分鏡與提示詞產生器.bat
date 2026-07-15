@echo off
chcp 65001 > nul
title 消防演習分鏡與 AI 提示詞產生器
echo.
echo ╔══════════════════════════════════════════╗
echo ║ 消防演習分鏡與提示詞產生器 (Port 8003)  ║
echo ║ 啟動後請至瀏覽器開啟：                 ║
echo ║ http://localhost:8003                  ║
echo ╚══════════════════════════════════════════╝
echo.
cd /d "%~dp0"
C:\Python313\python.exe app.py
pause
