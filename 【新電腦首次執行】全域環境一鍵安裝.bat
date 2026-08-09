@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo  ================================================================
echo   AI 專案全域環境一鍵安裝 (電腦僅需執行一次)
echo  ================================================================
echo.
echo  本程式將自動安裝 Python、Git 與所有 AI 系統所需套件
echo  安裝需要 5~15 分鐘，請保持網路連線
echo.
echo  [注意] 安裝過程中可能會要求系統管理員權限，請點選「是」
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0全域環境一鍵安裝.ps1"

echo.
pause
