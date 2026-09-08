# =====================================================================
# 🚀 鴻勝化學 QC 檢驗即時看板系統 一鍵環境安裝腳本 (setup_env.ps1)
# =====================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎨 檢查並安裝「鴻勝化學 QC 檢驗看板系統」依賴環境..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 檢查 Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✓ 偵測到 Python，正在安裝必要套件 (openpyxl, python-docx, pillow)..." -ForegroundColor Green
    python -m pip install --quiet openpyxl python-docx pillow
    Write-Host "✓ Python 套件安裝完成！" -ForegroundColor Green
} else {
    Write-Host "⚠️ 未偵測到 Python，若需執行本機伺服器與 Excel 解析，請安裝 Python 3.x。" -ForegroundColor Yellow
}

# 檢查 Node.js / Wrangler
if (Get-Command npx -ErrorAction SilentlyContinue) {
    Write-Host "✓ 偵測到 Node.js，支援 Wrangler Cloudflare Pages 快速部署。" -ForegroundColor Green
} else {
    Write-Host "ℹ️ 未偵測到 Node.js，如需部署到 Cloudflare，請安裝 Node.js。" -ForegroundColor Gray
}

Write-Host "`n🎉 環境檢查與設定完成！" -ForegroundColor Cyan
Write-Host "💡 提示：雙擊 2_PWA_App版/啟動PWA本機測試.bat 即可立即啟動測試！" -ForegroundColor Yellow
