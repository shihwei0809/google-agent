@echo off
chcp 65001 > nul
echo ==================================================
echo   Syncing projects in c:\GOOGLE ANGET to Obsidian...
echo ==================================================
echo.

cd /d "c:\GOOGLE ANGET\ai anget"
python sync_projects.py

echo.
echo ==================================================
echo   Sync complete! Press any key to close...
echo ==================================================
pause > nul
