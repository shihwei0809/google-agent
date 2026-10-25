@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
"C:\Python313\python.exe" main.py > wmi_test.log 2>&1