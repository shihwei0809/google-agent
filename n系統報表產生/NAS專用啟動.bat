@echo off
chcp 65001 >nul
title 生產履歷系統 - NAS連線啟動中...

:: 使用 pushd 解決 Windows 點擊 NAS (UNC路徑) 時可能出現的目錄錯誤問題
pushd "%~dp0"

echo ==========================================
echo       正在從 NAS 載入最新版系統...
echo ==========================================
echo.

python main.py

popd
pause
