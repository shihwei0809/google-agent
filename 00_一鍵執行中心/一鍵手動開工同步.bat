@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 正在執行開工同步 (整合 main 與 auto-backup 備份)...
echo ==================================================
powershell -ExecutionPolicy Bypass -File "%~dp0AutoStartWork.ps1"
pause
