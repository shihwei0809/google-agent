@echo off
cd /d "%~dp0"
echo 正在執行 Gmail 自動分類與歸檔...
.venv\Scripts\python.exe archive_organizer.py --limit 150
echo 整理完成！
