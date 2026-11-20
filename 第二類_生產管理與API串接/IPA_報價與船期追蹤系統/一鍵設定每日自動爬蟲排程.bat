@echo off
cd /d "%~dp0"
chcp 65001 >nul 2>&1
echo ======================================================
echo  IPA (異丙醇) 報價與船期系統 - 設定每日 08:00 自動爬蟲排程
echo ======================================================
echo.
echo [1/2] 立即執行一次今日報價與匯率抓取測試...
python daily_auto_scraper.py
echo.
echo [2/2] 註冊 Windows 工作排程器 (每天早上 08:00 自動背景執行)...
schtasks /Create /TN "IPA_Daily_Quote_Vessel_Scraper" /TR "python \"%~dp0daily_auto_scraper.py\"" /SC DAILY /ST 08:00 /F
echo.
echo ✅ 設定完成！系統將於每天早上 08:00 自動抓取並更新資料庫與 CSV 日報。
pause
