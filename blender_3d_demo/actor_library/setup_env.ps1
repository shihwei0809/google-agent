$ErrorActionPreference = "Stop"
Write-Host "[actor_library] Checking Python & Pillow..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

python -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pillow..." -ForegroundColor Yellow
    python -m pip install --upgrade pillow
}

New-Item -ItemType Directory -Force -Path "$PSScriptRoot\refs" | Out-Null
Write-Host "[actor_library] Environment ready." -ForegroundColor Green
