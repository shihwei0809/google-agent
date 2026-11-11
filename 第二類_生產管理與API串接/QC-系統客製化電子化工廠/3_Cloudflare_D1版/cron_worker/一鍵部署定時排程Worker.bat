@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ======================================================
echo 正在部署 QC 檢驗超時 24/7 背景定時排程 Worker 至 Cloudflare...
echo ======================================================
python deploy_cron.py
echo.
pause
