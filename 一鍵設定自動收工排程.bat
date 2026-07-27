@echo off
chcp 65001 > nul
echo ==================================================
echo 📅 正在設定每日 23:00 自動收工同步排程...
echo ==================================================
python "C:\GOOGLE ANGET\register_sync_task.py"
echo 🎉 排程設定完成！每日 23:00 將自動檢測變更並同步至 GitHub。
pause
