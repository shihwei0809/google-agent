@echo off
chcp 65001 > nul
echo ==================================================
echo   Syncing projects in %~dp0 to Obsidian...
echo ==================================================
echo.

cd /d "%~dp0\ai anget"
python sync_projects.py

echo.
echo ==================================================
echo   Sync complete! Press any key to close...
echo ==================================================
pause > nul
