# =====================================================================
# 🚀 三合一單與 COA 四重核對系統 (Cloudflare + R2 + PWA) 一鍵環境檢測腳本
# =====================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🔍 正在檢查「三合一單與 COA 四重核對 (Cloudflare + R2 + PWA)」專案環境..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. 檢查 Node.js 與 Wrangler CLI (用於 Cloudflare 部署)
if (Get-Command npx -ErrorAction SilentlyContinue) {
    Write-Host "✓ [已就緒] 偵測到 Node.js 與 npx 工具。" -ForegroundColor Green
} else {
    Write-Host "⚠️ [未安裝] 尚未偵測到 Node.js，如需部署至 Cloudflare 請安裝 Node.js (https://nodejs.org)。" -ForegroundColor Yellow
}

# 2. 檢查 Python (用於 PWA 本機測試)
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✓ [已就緒] 偵測到 Python 環境，可支援本機 PWA 測試伺服器。" -ForegroundColor Green
} else {
    Write-Host "⚠️ [未安裝] 尚未偵測到 Python，可選安裝以支援本機 PWA 離線測試伺服器。" -ForegroundColor Yellow
}

Write-Host "`n🎉 環境檢測完成！" -ForegroundColor Cyan
Write-Host "💡 提示：" -ForegroundColor Gray
Write-Host "  - 執行「一鍵啟動_Cloudflare本地測試.bat」可進行雲端邊緣模擬。" -ForegroundColor Gray
Write-Host "  - 進入「3_Cloudflare_R2_D1版」可執行「一鍵自動部署上雲端.bat」將系統發布至 Cloudflare Pages。" -ForegroundColor Gray
