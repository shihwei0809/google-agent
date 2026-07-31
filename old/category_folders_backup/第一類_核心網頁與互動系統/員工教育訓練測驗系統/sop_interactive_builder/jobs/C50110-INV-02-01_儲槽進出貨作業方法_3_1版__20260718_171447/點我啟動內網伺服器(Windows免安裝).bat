@echo off
chcp 65001 >nul 2>&1
echo.
echo  ============================================
echo   員工教育訓練測驗系統 — 啟動中...
echo  ============================================
echo.
echo  請稍候，伺服器啟動後，瀏覽器將自動開啟。
echo  若未自動開啟，請手動在瀏覽器輸入伺服器顯示的網址。
echo  *** 請勿關閉此視窗，關閉即停止服務 ***
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0serve_intranet.ps1"
pause
