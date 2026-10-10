@echo off
chcp 65001 > nul
echo ==================================================
echo Starting Local GUI System...
echo ==================================================
cd /d "%~dp0"
start pythonw main.py
exit
