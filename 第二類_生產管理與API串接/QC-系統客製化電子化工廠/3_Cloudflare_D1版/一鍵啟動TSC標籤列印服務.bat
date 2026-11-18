@echo off
chcp 65001 >nul
title 鴻勝化學 - TSC 網路標籤機 (192.168.3.128) 列印代理服務
cd /d "%~dp0"

echo 正在啟動 TSC 標籤機列印代理服務...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tsc_print_proxy.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [提示] 若出現權限錯誤，請嘗試「按右鍵 - 以系統管理員身分執行」。
    pause
)
