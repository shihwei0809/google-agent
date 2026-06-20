@echo off
chcp 65001 > nul
echo 正在請求管理員權限以啟動排程設定...
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_schedule.ps1"
