@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo ========================================================
echo   ISOTANK 槽車編號與三合一單 資材課4cm條碼生成器
echo ========================================================
echo.

python "%~dp0add_isotank_code.py"

pause
