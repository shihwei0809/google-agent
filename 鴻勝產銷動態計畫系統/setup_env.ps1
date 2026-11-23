$ErrorActionPreference = "Stop"
Write-Host "=== 鴻勝產銷動態計畫系統 - 環境初期化 (setup_env.ps1) ===" -ForegroundColor Cyan

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[錯誤] 找不到 Python，請先安裝 Python 3.10+" -ForegroundColor Red
    exit 1
}

Write-Host "Python 版本: $(& python --version)" -ForegroundColor Green

$reqFile = Join-Path $PSScriptRoot "2_PWA_App版\requirements.txt"
if (Test-Path $reqFile) {
    Write-Host "正在檢查並安裝 Python 相依套件 ($reqFile)..." -ForegroundColor Yellow
    & python -m pip install --upgrade pip
    & python -m pip install -r $reqFile
}

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    Write-Host "Node.js 版本: $(& node -v)" -ForegroundColor Green
} else {
    Write-Host "[提醒] 未偵測到 Node.js；若需部署至 Cloudflare 請先安裝 Node.js。" -ForegroundColor Yellow
}

$docScript = Join-Path $PSScriptRoot "build_manual_doc.py"
if (Test-Path $docScript) {
    Write-Host "正在重新產生操作手冊 .docx..." -ForegroundColor Yellow
    & python $docScript
}

Write-Host "=== 環境設定完成！可執行 2_PWA_App版\啟動PWA本機測試.bat ===" -ForegroundColor Green
