@echo off
chcp 65001 >nul
echo ========================================================
echo   Cloudflare Pages + D1 雲端資料庫 自動化部署工具
echo ========================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"
pause
