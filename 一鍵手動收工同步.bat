@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 正在執行手動收工同步 (Git Commit ^& Push)...
echo ==================================================
powershell -ExecutionPolicy Bypass -File "C:\GOOGLE ANGET\AutoSync_OffWork.ps1"
pause
