@echo off
chcp 65001 >nul 2>&1
title Cloudflare PWA Deploy
color 0B
cd /d "%~dp0..\教育訓練教材\2_PWA_App版"
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "setup_env.ps1"
pause
