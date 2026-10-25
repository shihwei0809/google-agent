@echo off
chcp 65001 >nul 2>&1
title 公司電腦 - Cloudflare RDP 遠端桌面穿透中心
cd /d "%~dp0"

echo ============================================================
echo   正在啟動 Cloudflare HTTPS 443 專屬穿透 (微軟原生 RDP 模式)
echo ============================================================
echo.

python rdp_tunnel.py

pause
