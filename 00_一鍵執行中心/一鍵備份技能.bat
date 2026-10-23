@echo off
chcp 65001 > nul
echo 正在啟動 Anti-Gravity 技能一鍵備份...
PowerShell.exe -ExecutionPolicy Bypass -File "%~dp0backup_skills.ps1"
pause
