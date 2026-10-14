@echo off
chcp 65001 >nul
title 回收液照片 - 依週分類歸檔工具
echo ===================================================
echo   【回收液照片歸檔】依週分類歸檔工具
echo   自動建立：YYYY年第WW週 (MM.DD~MM.DD) 資料夾
echo ===================================================
echo.
node "%~dp0organize_photos.js"
echo.
echo 執行完畢，按任意鍵關閉視窗...
pause >nul
