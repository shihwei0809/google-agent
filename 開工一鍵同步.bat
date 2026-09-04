@echo off
chcp 65001 >nul
title 跨電腦開工 - 三軌合一智慧對齊
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0AutoSync_StartWork.ps1"
echo.
echo 按任意鍵關閉視窗...
pause >nul