@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo   ISOTANK 槽車編號【一鍵拖曳/貼上】3cm條碼產生器
echo ========================================================
echo.

python add_isotank_code.py

pause
