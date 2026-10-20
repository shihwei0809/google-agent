# HTTPS 遠端網頁穿透中心 一鍵環境設定腳本
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  HTTPS 遠端網頁穿透中心 - 環境初始化" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. 檢查 Python
try {
    $pyVer = python --version 2>&1
    Write-Host "[✓] 偵測到 Python: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[!] 未安裝 Python，請至 https://python.org 安裝" -ForegroundColor Red
    exit 1
}

# 2. 安裝必要 pip 套件
$reqFile = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $reqFile) {
    Write-Host "[*] 正在確認必要 Python 套件..." -ForegroundColor Yellow
    python -m pip install -r $reqFile --quiet
    Write-Host "[✓] Python 套件已就緒！" -ForegroundColor Green
}

# 3. 檢查 cloudflared.exe
$cloudflaredPath = Join-Path (Split-Path $PSScriptRoot -Parent) "cloudflared.exe"
if (Test-Path $cloudflaredPath) {
    Write-Host "[✓] 偵測到 Cloudflare 穿透工具: $cloudflaredPath" -ForegroundColor Green
} else {
    Write-Host "[*] 正在下載 Cloudflare 穿透工具..." -ForegroundColor Yellow
    curl.exe -L --ssl-no-revoke -o $cloudflaredPath "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Write-Host "[✓] Cloudflare 穿透工具下載完成！" -ForegroundColor Green
}

Write-Host "`n[✓] 環境檢查與初始化完成！" -ForegroundColor Cyan
