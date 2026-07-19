@echo off
chcp 65001 >nul
title SOP Interactive Builder
cd /d "%~dp0"
echo =========================================================
echo  SOP Interactive Builder is starting...
echo  The browser will open automatically.
echo  Keep this window open to run the server.
echo =========================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python not found. Please install Python and add to PATH.
    pause
    exit /b
)
if not exist "venv\Scripts\python.exe" (
    echo [Setup] Creating Python virtual environment...
    python -m venv venv
)
echo [Setup] Checking and installing requirements (this may take a moment)...
venv\Scripts\python.exe -m pip install -q -r requirements.txt
if not exist "jobs" mkdir jobs
if not exist "templates" mkdir templates

cls
echo ===============================================================================
echo  SOP Interactive Builder is starting...
echo  The browser will open automatically in 2 seconds.
echo  Keep this window open to run the server.
echo ===============================================================================
echo 📱 員工教育訓練互動簡報產生器 - 本機伺服器已啟動
echo ===============================================================================
echo.
echo 💡 請將此視窗保持開啟，關閉後服務將中斷。
echo.
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback|vEthernet' } | Select-Object -First 1).IPAddress"`) do set LOCAL_IP=%%i

echo 📢 請在瀏覽器輸入以下網址開啟產生器：
echo 👉 本機使用: http://localhost:8000
if defined LOCAL_IP (
    echo 👉 區網分享: http://%LOCAL_IP%:8000  ^(傳給其他同事^)
)
echo ===============================================================================
timeout /t 2 >nul
start http://localhost:8000
venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000 --log-level warning
pause
