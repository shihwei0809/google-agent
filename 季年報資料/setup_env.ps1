param(
    [switch]$DeployCloudflare
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  鴻勝資材部｜季年報智慧分析系統 — 環境設定與部署腳本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check Python & pip packages
Write-Host "`n[1/3] 檢查 Python 與必要套件..." -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[錯誤] 找不到 Python，請先安裝 Python 3.10+ 並勾選 Add to PATH。" -ForegroundColor Red
    exit 1
}
$pkgs = @("fastapi", "uvicorn", "openpyxl", "python-docx", "pillow")
foreach ($p in $pkgs) {
    Write-Host "  - 確認套件: $p"
    python -m pip install $p -q
}

# 2. Sync frontend across 3 tracks
Write-Host "`n[2/3] 同步三軌前端檔案..." -ForegroundColor Yellow
Copy-Item "$RootDir\2_PWA_App版\index.html","$RootDir\2_PWA_App版\app.js","$RootDir\2_PWA_App版\seed_data.js","$RootDir\2_PWA_App版\pwa_offline_sync.js" "$RootDir\1_Web_網頁版\" -Force
Copy-Item "$RootDir\2_PWA_App版\index.html","$RootDir\2_PWA_App版\app.js","$RootDir\2_PWA_App版\seed_data.js","$RootDir\2_PWA_App版\pwa_offline_sync.js","$RootDir\2_PWA_App版\manifest.json","$RootDir\2_PWA_App版\sw.js" "$RootDir\3_Cloudflare_D1版\public\" -Force
Write-Host "  - 三軌前端檔案同步完成！" -ForegroundColor Green

# 3. Optional Cloudflare D1 Deployment
if ($DeployCloudflare) {
    Write-Host "`n[3/3] 啟動 Cloudflare Pages + D1 自動部署..." -ForegroundColor Yellow
    $cfDir = Join-Path $RootDir "3_Cloudflare_D1版"
    Push-Location $cfDir
    try {
        $toml = Get-Content "wrangler.toml" -Raw
        if ($toml -match "REPLACE_WITH_YOUR_D1_DATABASE_ID") {
            Write-Host "  [提示] 尚未設定 D1 database_id，嘗試自動建立 D1 資料庫 hs-material-report-db..." -ForegroundColor Cyan
            npx wrangler d1 create hs-material-report-db
            Write-Host "  [請注意] 請將上方產生的 database_id 貼入 3_Cloudflare_D1版\wrangler.toml 後，再次執行本腳本！" -ForegroundColor Yellow
            exit 0
        }
        Write-Host "  - 套用 D1 資料表結構 (schema.sql)..."
        npx wrangler d1 execute hs-material-report-db --remote --file=./schema.sql
        Write-Host "  - 部署至 Cloudflare Pages..."
        npx wrangler pages deploy public --project-name=hs-material-quarterly-report
        Write-Host "`n[完成] Cloudflare Pages + D1 部署成功！" -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Host "`n[3/3] 環境初始化完成！" -ForegroundColor Green
    Write-Host "  - 本機測試請雙擊：2_PWA_App版\啟動PWA本機測試.bat"
    Write-Host "  - 上雲部署請執行：.\setup_env.ps1 -DeployCloudflare"
}
