# =====================================================================
# 🚀 hongsheng-web 專案環境一鍵設定腳本 (setup_env.ps1)
# =====================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎨 開始檢查並安裝「hongsheng-web」專案環境..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 純靜態專案環境檢查
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "✓ 偵測到 Node.js，可使用 live-server 快速載入網頁。" -ForegroundColor Green
} else {
    Write-Host "✓ 本專案為純前端網頁，無須特殊依賴環境，直接雙擊 index.html 即可運行。" -ForegroundColor Green
}

Write-Host "`n🎉 環境設定檢查結束！" -ForegroundColor Cyan
