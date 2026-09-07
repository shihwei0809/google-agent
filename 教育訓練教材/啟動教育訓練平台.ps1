# AI Training Platform Launcher
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$pip = Join-Path $backend "venv\Scripts\pip.exe"
$python = Join-Path $backend "venv\Scripts\python.exe"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  AI Training Platform - Smart Launcher" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Step 1: Backend venv
Write-Host "`n[1/4] Checking backend..." -ForegroundColor Yellow
if (-not (Test-Path $python)) {
    Write-Host "      Creating Python venv..." -ForegroundColor Gray
    python -m venv "$backend\venv"
}

# Step 2: Backend packages
if (-not (Test-Path "$backend\venv\Lib\site-packages\fastapi")) {
    Write-Host "      Installing backend packages..." -ForegroundColor Gray
    & $pip install -r "$backend\requirements.txt" --trusted-host pypi.org --trusted-host files.pythonhosted.org --retries 5 --timeout 120
} else {
    Write-Host "      [OK] Backend packages ready." -ForegroundColor Green
}

# Step 3: Frontend packages
Write-Host "`n[2/4] Checking frontend..." -ForegroundColor Yellow
$viteCmd = Join-Path $frontend "node_modules\.bin\vite.cmd"
if (-not (Test-Path $viteCmd)) {
    Write-Host "      Installing npm packages..." -ForegroundColor Gray
    npm config set strict-ssl false
    Set-Location $frontend
    npm install
    npm config set strict-ssl true
    Set-Location $root
}

# Step 4: rolldown binding
$rolldownPath = Join-Path $frontend "node_modules\@rolldown\binding-win32-x64-msvc"
if (-not (Test-Path $rolldownPath)) {
    Write-Host "      Installing Vite native binding..." -ForegroundColor Gray
    Set-Location $frontend
    npm install @rolldown/binding-win32-x64-msvc --save-optional
    Set-Location $root
}
Write-Host "      [OK] Frontend ready." -ForegroundColor Green

# Step 5: Start Backend
Write-Host "`n[3/4] Starting FastAPI backend (Port: 8000)..." -ForegroundColor Yellow
Start-Process "cmd" -ArgumentList "/k cd /d `"$backend`" && `"$python`" -m uvicorn main:app --host 0.0.0.0 --port 8000" -WindowStyle Normal
Start-Sleep -Seconds 2

# Step 6: Start Frontend
Write-Host "[4/4] Starting React frontend (Port: 5173)..." -ForegroundColor Yellow
Start-Process "cmd" -ArgumentList "/k cd /d `"$frontend`" && npm run dev -- --host" -WindowStyle Normal
Start-Sleep -Seconds 4

# Step 7: Open browser
Start-Process "http://localhost:5173"

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "  Platform started!" -ForegroundColor Green
Write-Host "  Web: http://localhost:5173" -ForegroundColor White
Write-Host "  API: http://localhost:8000" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Green
Write-Host "`nPress Enter to close this launcher..." -ForegroundColor Gray
Read-Host