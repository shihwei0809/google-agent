@echo off
title OCR Compare Tool Launcher
echo [*] Checking and installing required packages (pymupdf, easyocr)...
python -m pip install pymupdf easyocr
echo [*] Launching OCR Compare Tool...
python ocr_compare_tool.py
pause
