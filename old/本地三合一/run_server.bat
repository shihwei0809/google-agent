@echo off
title Local OCR Server Launcher
echo [*] Checking and installing required Python packages...
python -m pip install fastapi uvicorn easyocr pillow
echo [*] Starting Python OCR Server...
python ocr_server.py
pause
