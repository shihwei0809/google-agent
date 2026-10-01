# setup_env.ps1: 一鍵部署環境至 Cloudflare Pages + D1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Cloudflare Pages + D1 一鍵部署環境" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 檢查 npm
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "未安裝 Node.js (npm)，請先安裝 Node.js！" -ForegroundColor Red
    exit
}

# 安裝 wrangler CLI
Write-Host "正在檢查並安裝 Wrangler CLI..."
npm install -g wrangler

# 登入 Cloudflare
Write-Host "`n準備登入 Cloudflare，請在彈出的瀏覽器視窗中授權..." -ForegroundColor Yellow
wrangler login

# 建立 D1 資料庫
Write-Host "`n正在建立 D1 資料庫 (weather-monitor-db)..."
$d1Info = wrangler d1 create weather-monitor-db | Out-String

# 解析 database_id 並回填至 wrangler.toml
if ($d1Info -match "database_id = `"(.+?)`"") {
    $dbId = $matches[1]
    Write-Host "取得 Database ID: $dbId" -ForegroundColor Green
    
    $tomlPath = "wrangler.toml"
    $tomlContent = Get-Content $tomlPath
    $tomlContent = $tomlContent -replace 'database_id = ""', "database_id = `"$dbId`""
    Set-Content -Path $tomlPath -Value $tomlContent
    Write-Host "已自動回填 database_id 至 wrangler.toml" -ForegroundColor Green
} else {
    Write-Host "建立資料庫失敗或資料庫已存在，跳過回填。" -ForegroundColor Yellow
}

# 初始化資料庫結構
Write-Host "`n正在寫入資料庫 Schema..."
wrangler d1 execute weather-monitor-db --file=schema.sql --remote

# 部署至 Cloudflare Pages
Write-Host "`n正在部署專案至 Cloudflare Pages..."
wrangler pages deploy public --project-name weather-monitor-pwa

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host " 部署完成！" -ForegroundColor Green
Write-Host " 請記下上方輸出的網址，即可隨時查看溫度儀表板。"
Write-Host " (每 10 分鐘自動監控的功能已經透過 Cron Triggers 生效)"
Write-Host "==========================================" -ForegroundColor Cyan
