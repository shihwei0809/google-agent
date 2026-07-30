# family-file-hub setup script with WAN, Waitress & Ngrok auto-deployment
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process -ErrorAction SilentlyContinue

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Starting Family File Hub Cross-Device Setup..." -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Python not found! Please install Python 3.8+." -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version
Write-Host "Detected Python: $pythonVersion" -ForegroundColor Green

# Create venv
$venvPath = Join-Path $PSScriptRoot "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment (venv)..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Virtual environment created!" -ForegroundColor Green
}

# Install dependencies
$pipExe = Join-Path $venvPath "Scripts\pip.exe"
Write-Host "Installing dependencies (Flask, qrcode, pillow, waitress, pyngrok)..." -ForegroundColor Yellow
& $pipExe install --upgrade pip
& $pipExe install flask qrcode pillow waitress pyngrok

# Download ngrok.exe automatically if not found anywhere on system
$ngrokPath = Join-Path $PSScriptRoot "ngrok.exe"
$ngrokInPath = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokInPath -and -not (Test-Path $ngrokPath) -and -not (Test-Path "C:\ngrok\ngrok.exe")) {
    Write-Host "Downloading portable ngrok.exe for cross-computer WAN tunnel..." -ForegroundColor Yellow
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $zipPath = Join-Path $PSScriptRoot "ngrok.zip"
        Invoke-WebRequest -Uri "https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-windows-amd64.zip" -OutFile $zipPath
        Expand-Archive -Path $zipPath -DestinationPath $PSScriptRoot -Force
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        Write-Host "ngrok.exe deployed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Automatic ngrok download skipped." -ForegroundColor Yellow
    }
} else {
    Write-Host "ngrok executable detected!" -ForegroundColor Gray
}

Write-Host "=====================================================" -ForegroundColor Green
Write-Host "Setup Completed Successfully!" -ForegroundColor Green
Write-Host "Run 'python app.py' or double click '一鍵啟動.bat' to start." -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Green
