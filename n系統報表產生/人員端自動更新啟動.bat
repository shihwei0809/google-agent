@echo off
chcp 65001 >nul
title 生產履歷系統 - 自動更新啟動器
color 0B

echo ==========================================
echo       生產履歷系統 - 檢查更新中...
echo ==========================================
echo.

:: 【請修改這裡】：將這行換成您們公司 NAS 放最新版 main.py 的資料夾路徑
:: 例如：set NAS_PATH=\\192.168.1.100\公用槽\N系統最新版
set NAS_PATH=\\請替換為NAS的實際路徑\N系統最新發布區

:: 檢查 NAS 路徑是否連線成功
if not exist "%NAS_PATH%" (
    echo [警告] 無法連線至 NAS 伺服器 (%NAS_PATH%)。
    echo 將略過更新，直接使用本機現有版本啟動...
    echo.
    timeout /t 3 >nul
    goto START_APP
)

:: 使用 robocopy 從 NAS 抓取最新的 main.py 到本機 (只會抓較新的檔案)
echo [進度] 發現 NAS 伺服器，正在同步最新程式碼...
robocopy "%NAS_PATH%" "%~dp0\" main.py /XO /NJH /NJS /NDL /NC /NS >nul 2>&1

echo [成功] 更新檢查完畢！
echo.

:START_APP
echo 啟動系統中，請稍候...
python "%~dp0main.py"

pause
