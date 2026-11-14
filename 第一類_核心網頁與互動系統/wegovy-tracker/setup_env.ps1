# setup_env.ps1 - 一鍵環境設定腳本
Write-Host "=== 正在檢查 Wegovy Tracker 環境相依 ===" -ForegroundColor Cyan

# 檢查 Node.js / npm
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Node.js / npm 已安裝" -ForegroundColor Green
} else {
    Write-Host "[WARNING] 未偵測到 Node.js，如需執行 wrangler 部署請先安裝 Node.js" -ForegroundColor Yellow
}

# 檢查 Wrangler CLI
if (Get-Command wrangler -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Cloudflare Wrangler CLI 已安裝" -ForegroundColor Green
} else {
    Write-Host "[INFO] 正在安裝 Wrangler CLI..." -ForegroundColor Yellow
    npm install -g wrangler
}

Write-Host "=== 環境檢查完成！直接執行 '一鍵部署至Cloudflare.bat' 即可部署上線 ===" -ForegroundColor Cyan
