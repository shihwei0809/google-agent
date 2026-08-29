@echo off
chcp 65001 >nul
title TSMC Lorry Barcode Server

cd /d "%~dp0"

python -c "import fastapi, uvicorn, openpyxl, qrcode, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    pip install fastapi uvicorn openpyxl qrcode pillow --disable-pip-version-check -q >nul 2>&1
)

start "" "http://localhost:8002"
cls
python server.py
