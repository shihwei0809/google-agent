@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 正在將 [auto-backup] 備份分支正式發布至 main 主線...
echo ==================================================
powershell -ExecutionPolicy Bypass -File "C:\GOOGLE ANGET\PublishToMain.ps1"
pause
