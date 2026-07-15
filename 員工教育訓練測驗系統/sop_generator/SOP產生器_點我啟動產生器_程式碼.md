# 程式碼備份與修改紀錄: 點我啟動產生器(Windows免安裝).bat

本文件為 `點我啟動產生器(Windows免安裝).bat` 的程式碼備份，便於後續版本比對與修改紀錄追蹤。

## 原始程式碼

```batch
@echo off
title Start SOP Quiz Generator Manager
echo ============================================================
echo   SOP Quiz Generator Manager is starting...
echo   The browser will open automatically in 2 seconds.
echo   Keep this window open to run the server.
echo ============================================================
cd /d "%~dp0"
start http://localhost:18082/index.html
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_intranet.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start server.
    pause
)

```
