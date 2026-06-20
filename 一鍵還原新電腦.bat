@echo off
chcp 65001 > nul
echo 正在請求管理員權限以啟動新電腦環境還原與部署...
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_new_computer.ps1"
