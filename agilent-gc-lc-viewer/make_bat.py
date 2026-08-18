# Write BAT in UTF-8 (No BOM) so both VS Code/Notepad and CMD display clean Chinese
bat_content = """@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

title Agilent GC/LC Chromatography Data Viewer

echo ======================================================
echo    Agilent GC/LC 層析數據解析系統
echo ======================================================
echo.
echo 正在檢查環境並啟動服務...
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [!] 啟動遇到問題，正在執行一鍵環境安裝 (setup_env.ps1)...
    powershell -ExecutionPolicy Bypass -File .\\setup_env.ps1
    echo 環境修復完成，重新啟動中...
    python main.py
)

pause
"""

with open("點我啟動Agilent數據解析器.bat", "w", encoding="utf-8") as f:
    f.write(bat_content)

print("Saved BAT cleanly in UTF-8 without BOM!")
