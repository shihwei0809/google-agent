param (
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\setup_env.ps1"
    Write-Host "This script checks and installs required python packages for this tool."
    exit
}

Write-Host "=== 勝一小包barcode對刷核對 環境設定 ===" -ForegroundColor Cyan

# 檢查 Python
$pythonPath = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "[錯誤] 找不到 Python，請手動安裝並加入 PATH" -ForegroundColor Red
    exit 1
}

Write-Host "檢查並安裝 pip 套件..." -ForegroundColor Yellow
$requirements = @("fastapi", "uvicorn")

foreach ($pkg in $requirements) {
    Write-Host "安裝 $pkg ..."
    python -m pip install $pkg
}

Write-Host "環境設定完成！您可以雙擊 [啟動掃描系統.bat] 開始執行。" -ForegroundColor Green
