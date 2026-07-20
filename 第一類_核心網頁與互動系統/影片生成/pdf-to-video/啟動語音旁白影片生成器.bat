@echo off
title PDF Video Generator (Port 8002)
cd /d "%~dp0"

for /f "tokens=*" %%a in ('powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object IPAddress -notlike '127.*' | Where-Object IPAddress -notlike '169.254.*' | Select-Object -ExpandProperty IPAddress)[0]"') do set LOCAL_IP=%%a

echo ===================================================
echo    PDF Video Generator (Port 8002)
echo.
echo    本機開啟網址:
echo    http://localhost:8002
echo.
echo    同網域 / 旁人使用網址:
echo    http://%LOCAL_IP%:8002
echo ===================================================
echo.

python app.py
pause
