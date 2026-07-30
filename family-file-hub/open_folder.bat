@chcp 65001 >nul
@echo off
title Open Uploads Folder
cd /d "%~dp0"
if not exist uploads (
    mkdir uploads
)
explorer uploads
