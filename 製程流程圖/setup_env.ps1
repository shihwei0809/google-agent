Write-Host "正在安裝與部署 ChemFlow Pro 雲端版..."
npm install -g wrangler

Write-Host "登入 Cloudflare..."
wrangler login

Write-Host "建立 D1 資料庫..."
$dbOutput = wrangler d1 create chemflow_pro_db
$dbId = ($dbOutput | Select-String -Pattern "database_id = `"(.+?)`"").Matches.Groups[1].Value

if ($dbId) {
    Write-Host "取得 Database ID: $dbId"
    (Get-Content wrangler.toml) -replace 'database_id = ""', "database_id = `"$dbId`"" | Set-Content wrangler.toml
}

Write-Host "初始化資料表..."
wrangler d1 execute chemflow_pro_db --file=schema.sql --remote

Write-Host "部署至 Cloudflare Pages..."
wrangler pages deploy public --project-name chemflow-pro

Write-Host "部署完成！請至 Cloudflare Dashboard 設定環境變數 GEMINI_KEYS 與 OPENAI_KEYS。"