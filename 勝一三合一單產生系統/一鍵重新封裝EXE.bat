@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo   [勝一三合一單產生系統] 正在重新封裝 EXE 執行檔...
echo ========================================================
echo.

python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "勝一三合一單產生系統" ^
    --splash "splash.png" ^
    --add-data "台積電槽車barcode三合一單-範本.xlsx;." ^
    --add-data "地點代號對照表.xlsx;." ^
    --add-data "L269100_SEP73E4_COA.csv;." ^
    --add-data "L2C9100_SEP73E5_COA.csv;." ^
    --add-data "L2C9173_CPNE4R_COA.csv;." ^
    --add-data "L2C9501_PMAHQ_COA.csv;." ^
    --add-data "L2R9501_PMAHQR_COA.csv;." ^
    --add-data "Chemical_Lorry_L269100_SEP73E4.xlsx;." ^
    --add-data "Chemical_Lorry_L2C9100_SEP73E5.xlsx;." ^
    --add-data "Chemical_Lorry_L2C9173_CPNE4R.xlsx;." ^
    --add-data "Chemical_Lorry_L2C9501_PMAHQ.xlsx;." ^
    --add-data "Chemical_Lorry_L2R9501_PMAHQR.xlsx;." ^
    --exclude-module torch ^
    --exclude-module scipy ^
    --exclude-module pandas ^
    --exclude-module matplotlib ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [成功] 封裝完成！複製 EXE 至當前目錄...
    echo ========================================================
    copy /Y "dist\勝一三合一單產生系統.exe" ".\勝一三合一單產生系統.exe"
    echo   完成！您可以直接雙擊 [勝一三合一單產生系統.exe] 測試。
) else (
    echo.
    echo [錯誤] 打包過程發生異常，請檢查上方輸出訊息。
)
pause
