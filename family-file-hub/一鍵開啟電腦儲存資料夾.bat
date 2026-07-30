@echo off
cd /d "%~dp0"
title 開啟家庭檔案儲存目錄
if not exist uploads (
    mkdir uploads
)
explorer uploads
