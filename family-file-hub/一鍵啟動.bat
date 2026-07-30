@echo off
cd /d "%~dp0"
title 家庭手機檔案傳輸中心 (Family File Hub)
echo =====================================================
echo 正在啟動 家庭手機檔案傳輸中心 (Family File Hub)...
echo =====================================================
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe app.py
) else (
    python app.py
)
pause
