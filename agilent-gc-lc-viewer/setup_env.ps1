# PowerShell One-Click Environment Setup for Agilent GC/LC Data Viewer
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🧪 安裝 Agilent GC/LC 數據解析器依賴套件..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Python
try {
    $pythonVer = python --version 2>&1
    Write-Host "✅ 偵測到 Python: $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "❌ 系統未偵測到 Python，請先安裝 Python 3.8 或以上版本！" -ForegroundColor Red
    Exit 1
}

# Install required packages
$packages = @("fastapi", "uvicorn", "numpy", "pandas", "openpyxl", "python-multipart")

foreach ($pkg in $packages) {
    Write-Host "📦 檢查 / 安裝套件: $pkg ..." -ForegroundColor Yellow
    pip install $pkg --quiet
}

Write-Host "==========================================" -ForegroundColor Green
Write-Host "🎉 環境建置完成！請雙擊 點我啟動Agilent數據解析器.bat 啟動服務。" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
