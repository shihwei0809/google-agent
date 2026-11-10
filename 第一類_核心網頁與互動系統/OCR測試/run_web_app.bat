@echo off
cd /d "%~dp0"
title AI OCR to Excel Server
set PYTHONWARNINGS=ignore
python ocr_web_app.py
pause
