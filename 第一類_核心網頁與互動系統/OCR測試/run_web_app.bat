@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AI OCR to Excel Server
set PYTHONWARNINGS=ignore

echo ==============================================================
echo   AI 圖片/PDF 智慧判讀轉 Excel 系統 (OCR to Excel)
echo   正在啟動本機伺服器中，請稍候...
echo ==============================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 找不到 Python，請確認已安裝 Python 3.9 以上！
    pause
    exit /b 1
)

if not exist "outputs" mkdir outputs

echo [*] 正在載入 EasyOCR 雙語辨識模型 (繁體中文 + 英文)...
echo [*] 載入模型需約 5-10 秒，完成後系統將「自動彈出網頁瀏覽器」！
echo [*] 請保持此黑底視窗開啟，不要關閉。
echo.

python ocr_web_app.py

if %errorlevel% neq 0 (
    echo.
    echo [錯誤] 伺服器異常中斷！
    pause
)
