@echo off
chcp 65001 >nul
title 清理卡死 Git 程序

echo ======================================================
echo    正在清理背景卡死 / 佔用 CPU 的 Git 程序...
echo ======================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "d:\GOOGLE ANGET\scripts\clean_stuck_git.ps1" -ForceAll

echo.
echo ======================================================
echo    清理完成！已釋放 CPU 與記憶體資源。
echo    詳細記錄已儲存於: d:\GOOGLE ANGET\scripts\clean_git.log
echo ======================================================
echo.
timeout /t 3
