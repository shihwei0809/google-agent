@echo off
echo =========================================
echo  Chemical Warehouse - MD to Word Converter v3
echo =========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python first.
    timeout /t 5
    exit /b
)

REM Check and install dependencies
echo Checking dependencies...
python -c "import docx" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing python-docx...
    pip install python-docx
)

echo Starting conversion...
python md_to_word_v4.py

echo.
echo Conversion completed successfully!
timeout /t 3
