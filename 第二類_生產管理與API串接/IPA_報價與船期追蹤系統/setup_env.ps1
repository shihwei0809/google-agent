param(
    [switch]$DeployCloudflare
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " 🧪🚢 IPA (異丙醇) 報價與出貨單船期自動追蹤系統 - 環境設定" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. 檢查 Python
Write-Host "`n[1/4] 檢查 Python 環境..." -ForegroundColor Yellow
$pyVer = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 找不到 Python，請先安裝 Python 3.9+ 並加入 PATH。" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 已安裝: $pyVer" -ForegroundColor Green

# 2. 安裝必要 Python 套件
Write-Host "`n[2/4] 檢查並安裝必要 Python 套件 (requests, pillow, python-docx)..." -ForegroundColor Yellow
python -m pip install requests pillow python-docx -q
Write-Host "✅ Python 套件準備完成" -ForegroundColor Green

# 3. 初始化資料庫與執行首次每日爬蟲測試
Write-Host "`n[3/4] 初始化 SQLite 資料庫並同步今日最新匯率與雙單位報價..." -ForegroundColor Yellow
python .\daily_auto_scraper.py

# 4. 產出最新操作手冊
Write-Host "`n[4/4] 自動產出 Word 操作手冊..." -ForegroundColor Yellow
if (Test-Path ".\build_manual_doc.py") {
    python .\build_manual_doc.py
}

if ($DeployCloudflare) {
    Write-Host "`n[Cloudflare 部署] 準備部署 3_Cloudflare_D1版 至 Cloudflare Pages..." -ForegroundColor Cyan
    Set-Location "$ProjectRoot\3_Cloudflare_D1版"
    npx wrangler pages deploy public --project-name ipa-quote-vessel-tracker
    Set-Location $ProjectRoot
}

Write-Host "`n🎉 環境設定與初始化全部完成！可雙擊 [2_PWA_App版\啟動PWA本機測試.bat] 開啟系統。" -ForegroundColor Green
