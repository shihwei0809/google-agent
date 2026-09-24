@echo off
title 內網伺服器已啟動(無須安裝Python)
chcp 65001 > nul
cd /d "%~dp0"

:: 使用 PowerShell 執行本機伺服器腳本，並繞過執行原則限制
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_intranet.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [錯誤] 伺服器異常中斷。
    pause
)
