@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ========================================================
echo   AI 面試語音特質與資材適性分析系統 啟動中...
echo ========================================================

:: 1. 檢測 .venv 是否能在本機正常運作 (防範跨電腦複製硬編碼路徑錯誤)
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo [System] 檢測到非本機建立之舊 .venv 環境，自動清理中...
        rmdir /s /q ".venv" >nul 2>&1
    )
)

:: 2. 若環境不存在，執行一鍵自動安裝與環境設定
if not exist ".venv\Scripts\python.exe" (
    echo [System] 首次執行或尚未建置本機環境，正在自動執行一鍵安裝與依賴設定...
    powershell -ExecutionPolicy Bypass -File setup_env.ps1
    if errorlevel 1 (
        echo [Error] 環境安裝失敗，請檢查網路或 Python 安裝。
        pause
        exit /b
    )
)

:: 3. 測試環境套件
.venv\Scripts\python.exe -c "import fastapi, uvicorn, openpyxl, docx" >nul 2>&1
if errorlevel 1 (
    echo [System] 檢測到缺少必要套件，自動補全安裝中...
    powershell -ExecutionPolicy Bypass -File setup_env.ps1
)

:: 4. 啟動伺服器
echo [System] 啟動伺服器...
.venv\Scripts\python.exe main.py

if errorlevel 1 (
    echo [Error] 主程式中斷，嘗試以備用方式啟動...
    .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
)
pause