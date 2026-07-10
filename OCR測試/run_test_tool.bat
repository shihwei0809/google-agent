@echo off
title Local OCR Tester Launcher
echo [*] Checking and installing required packages (python-docx, python-pptx, pymupdf)...
python -m pip install python-docx python-pptx pymupdf easyocr
echo [*] Launching OCR Test Tool...
python ocr_test_tool.py
pause
