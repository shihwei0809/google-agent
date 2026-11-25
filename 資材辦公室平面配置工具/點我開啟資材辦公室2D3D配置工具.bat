@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
start "" "%~dp01_Web_網頁版\index.html"
