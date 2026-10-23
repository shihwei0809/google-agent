@echo off
chcp 65001 >nul
echo ========================================================
echo   Chrome 遠端桌面 (Chromoting) 服務一鍵重啟修復工具
echo ========================================================
echo.

:: 檢查是否具備管理員權限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 請務必「按右鍵」選擇「以系統管理員身分執行」！
    echo 正在嘗試自動請求管理員權限...
    powershell -Command "Start-Process cmd -ArgumentList '/c %~fn0' -Verb RunAs"
    exit /b
)

echo [1/3] 正在停止 Chrome 遠端桌面服務 (chromoting)...
net stop chromoting
taskkill /F /IM remoting_host.exe >nul 2>&1

echo [2/3] 等待 3 秒釋放連線狀態...
timeout /t 3 /nobreak >nul

echo [3/3] 正在重新啟動 Chrome 遠端桌面服務...
net start chromoting

echo.
echo ========================================================
echo  修復完成！請稍候 10~30 秒，至手機/遠端網頁重新整理檢查是否上線。
echo ========================================================
pause
