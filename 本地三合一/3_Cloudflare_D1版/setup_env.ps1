# Cloudflare Pages + D1 自動化部署腳本
Write-Host "開始部署 Cloudflare Pages 與 D1 資料庫..." -ForegroundColor Cyan

# 1. 確認是否安裝 wrangler
if (!(Get-Command "wrangler" -ErrorAction SilentlyContinue)) {
    Write-Host "未偵測到 wrangler，正在全域安裝..." -ForegroundColor Yellow
    npm install -g wrangler
}

# 2. 登入 Cloudflare (若已登入會自動跳過)
wrangler login

# 3. 建立 D1 資料庫
Write-Host "建立 D1 資料庫 (tsmc-verification-db)..." -ForegroundColor Cyan
$d1_output = wrangler d1 create tsmc-verification-db | Out-String

# 解析 database_id
$db_id = ""
if ($d1_output -match "database_id = `"(.+?)`"") {
    $db_id = $matches[1]
    Write-Host "成功獲取 Database ID: $db_id" -ForegroundColor Green
    
    # 4. 自動回填 wrangler.toml
    $toml_path = "wrangler.toml"
    $toml_content = Get-Content $toml_path
    $toml_content = $toml_content -replace "YOUR_DATABASE_ID_HERE", $db_id
    Set-Content $toml_path $toml_content
    Write-Host "已自動更新 wrangler.toml" -ForegroundColor Green
} else {
    Write-Host "警告：無法自動獲取 database_id，請檢查 wrangler.toml 是否已手動設定。" -ForegroundColor Yellow
}

# 5. 初始化資料表結構
Write-Host "建立資料表 (schema.sql)..." -ForegroundColor Cyan
wrangler d1 execute tsmc-verification-db --file=schema.sql --remote

# 6. 部署到 Cloudflare Pages
Write-Host "部署 PWA 至 Cloudflare Pages..." -ForegroundColor Cyan
wrangler pages deploy public --project-name=tsmc-check

Write-Host "✅ 部署完成！" -ForegroundColor Green

