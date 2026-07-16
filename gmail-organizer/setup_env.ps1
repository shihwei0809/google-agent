# setup_env.ps1 - Environment Setup Script for Gmail Organizer

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Gmail Organizer Environment Initialization" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Detect Python
$pythonCmd = "python"
$hasPython = $false

try {
    $ver = & python --version 2>&1
    if ($LASTEXITCODE -eq 0 -or $ver -like "*Python*") {
        Write-Host "Detected Python: $ver" -ForegroundColor Green
        $hasPython = $true
    }
} catch {
    # Ignore
}

if (-not $hasPython) {
    try {
        $ver = & py --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $ver -like "*Python*") {
            $pythonCmd = "py"
            Write-Host "Detected Python Launcher: $ver" -ForegroundColor Green
            $hasPython = $true
        }
    } catch {
        # Ignore
    }
}

if (-not $hasPython) {
    Write-Host "[ERROR] Python was not detected. Please install Python and add it to your PATH." -ForegroundColor Red
    Exit 1
}

# 2. Create Virtual Environment
if (-not (Test-Path -Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Yellow
    & $pythonCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        Exit 1
    }
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment .venv already exists. Skipping creation." -ForegroundColor Green
}

# 3. Install packages
Write-Host "Upgrading pip and installing Google API clients..." -ForegroundColor Yellow
& .venv\Scripts\python.exe -m pip install --upgrade pip
& .venv\Scripts\python.exe -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install packages." -ForegroundColor Red
    Exit 1
}

Write-Host "Dependencies installed successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "IMPORTANT REMINDER:" -ForegroundColor Yellow
Write-Host "Please download 'credentials.json' from Google Cloud Console" -ForegroundColor Yellow
Write-Host "and place it in this directory:" -ForegroundColor Yellow
Write-Host "  $PWD\credentials.json" -ForegroundColor Cyan
Write-Host "Then run: .venv\Scripts\python.exe organizer.py to start authentication." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
