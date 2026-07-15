@echo off
:: 切換工作目錄到批次檔所在的路徑，確保雙擊或以管理員權限執行時路徑正確
cd /d "%~dp0"
npm start
