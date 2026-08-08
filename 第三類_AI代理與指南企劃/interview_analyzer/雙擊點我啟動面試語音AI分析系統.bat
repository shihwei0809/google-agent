@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul 2>&1

echo.
echo  =====================================================
echo   AI 面試語音分析系統 - 啟動中...
echo  =====================================================
echo.
echo  正在執行環境自動偵測與安裝腳本，請稍候...
echo  (首次執行可能需要 1~3 分鐘安裝套件)
echo.

:: 使用 PowerShell 執行環境設定腳本
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_env.ps1"

if errorlevel 1 (
    echo.
    echo  [錯誤] 啟動失敗，請截圖以上訊息回報給系統管理員。
    echo.
    pause
)
