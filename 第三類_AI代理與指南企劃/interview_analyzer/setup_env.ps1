Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " [Setup] Initializing Interview AI System..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[Error] Python not found! Please install Python 3.9+ from https://python.org" -ForegroundColor Red
    Write-Host " - Make sure to check [Add Python to PATH] during installation!" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "[OK] Python found: $($pythonCmd.Source)" -ForegroundColor Green

# Create venv if not exists
if (-Not (Test-Path ".venv")) {
    Write-Host "[Info] Creating virtual environment .venv ..." -ForegroundColor Yellow
    python -m venv .venv
}

# Upgrade pip
Write-Host "[Info] Upgrading pip..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip -q

# Install requirements
Write-Host "[Info] Installing packages from requirements.txt ..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt python-docx

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host " [Success] Setup complete! Starting server..." -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green