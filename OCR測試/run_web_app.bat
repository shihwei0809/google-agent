@echo off
title DeckEdit Local Server Launcher
echo [*] Checking and installing required packages (fastapi, uvicorn, easyocr, docx, pptx, pymupdf, python-multipart)...
python -m pip install fastapi uvicorn easyocr python-docx python-pptx pymupdf python-multipart
echo [*] Launching DeckEdit Local Server...
python ocr_web_app.py
pause
