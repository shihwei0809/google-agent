param(
    [switch]$DeployCloudflare
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "=== 倉儲儲位 PWA 系統 - 環境設定 ===" -ForegroundColor Cyan

# 1. 檢查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[錯誤] 找不到 Python，請先安裝 Python 3.9+ 並勾選 Add to PATH。" -ForegroundColor Red
    exit 1
}

# 2. 安裝 Python 套件
Write-Host "[1/2] 安裝 Python 相依套件..." -ForegroundColor Yellow
python -m pip install -r "$ProjectRoot\2_PWA_App版\requirements.txt" -q

# 3. 確認必要目錄
New-Item -ItemType Directory -Force "$ProjectRoot\2_PWA_App版\data" | Out-Null
New-Item -ItemType Directory -Force "$ProjectRoot\backups" | Out-Null

if ($DeployCloudflare) {
    Write-Host "[2/2] 部署 3_Cloudflare_D1版 至 Cloudflare Pages..." -ForegroundColor Yellow
    if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
        Write-Host "[錯誤] 需要 Node.js / npx 才能執行 wrangler 部署。" -ForegroundColor Red
        exit 1
    }
    Set-Location "$ProjectRoot\3_Cloudflare_D1版"
    npx wrangler pages deploy ./public --project-name storage-rack-pwa
} else {
    Write-Host "[2/2] 環境安裝完成！可雙擊 2_PWA_App版\啟動PWA儲位系統.bat 啟動系統。" -ForegroundColor Green
}
