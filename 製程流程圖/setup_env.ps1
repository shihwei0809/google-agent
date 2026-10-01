Write-Host "開始在 Cloudflare 上部署 ChemFlow Pro 雲端環境..." -ForegroundColor Cyan
Write-Host "第一步：登入 Cloudflare (將自動開啟瀏覽器)" -ForegroundColor Yellow
npx wrangler login

Write-Host "第二步：建立 D1 雲端資料庫..." -ForegroundColor Yellow
$dbOutput = npx wrangler d1 create chemflow_pro_db
$dbOutput | Out-File -FilePath d1_output.txt

# 讀取輸出檔案並用正則表達式擷取 ID
$content = Get-Content d1_output.txt -Raw
$dbId = ""
if ($content -match 'database_id = "([^"]+)"') {
    $dbId = $matches[1]
}

if ($dbId) {
    Write-Host "成功取得 Database ID: $dbId" -ForegroundColor Green
    
    # 讀取並替換 wrangler.toml
    $tomlContent = Get-Content wrangler.toml -Raw
    # 如果原本有舊的 UUID，或是 local-test，直接用正則替換
    $tomlContent = $tomlContent -replace 'database_id = "[^"]*"', "database_id = `"$dbId`""
    Set-Content -Path wrangler.toml -Value $tomlContent
    
    Write-Host "第三步：初始化雲端資料庫資料表..." -ForegroundColor Yellow
    npx wrangler d1 execute chemflow_pro_db --file=schema.sql --remote

    Write-Host "第四步：發布至 Cloudflare Pages..." -ForegroundColor Yellow
    npx wrangler pages deploy public --project-name chemflow-pro
    
    Write-Host "部署完成！您可以前往您的 xxx.chemflow-pro.pages.dev 網站查看成果。" -ForegroundColor Green
    Write-Host "請記得前往 Cloudflare 儀表板，在該 Pages 專案的 Settings -> Environment Variables 設定您的 GEMINI_KEYS 與 OPENAI_KEYS！" -ForegroundColor Yellow
} else {
    Write-Host "無法自動擷取 Database ID，請檢查剛才建立 D1 資料庫的輸出內容。" -ForegroundColor Red
}

Remove-Item d1_output.txt -ErrorAction SilentlyContinue