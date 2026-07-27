@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 正在執行開工同步 (拉取 main 與 auto-backup 備份)...
echo ==================================================
powershell -ExecutionPolicy Bypass -File "C:\GOOGLE ANGET\AutoStartWork.ps1"
pause
