# PowerShell Environment Setup Script for pure-tts
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Setting up environment for pure-tts" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH! Please install Python 3.10+ first."
    Exit 1
}

Write-Host "Installing/Upgrading Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn edge-tts google-generativeai python-multipart httpx jinja2 requests

Write-Host "=============================================" -ForegroundColor Green
Write-Host "   Environment Setup Successfully Completed!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
