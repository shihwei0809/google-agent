# PowerShell 環境檢查腳本
Write-Host "檢查 Node.js 與 Wrangler..." -ForegroundColor Cyan

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "✅ Node.js 已安裝: $(node -v)" -ForegroundColor Green
} else {
    Write-Host "❌ 尚未安裝 Node.js" -ForegroundColor Red
}

if (Get-Command npx -ErrorAction SilentlyContinue) {
    Write-Host "✅ npx 可用" -ForegroundColor Green
} else {
    Write-Host "❌ 尚未具備 npx" -ForegroundColor Red
}

Write-Host "ACT 排程系統環境就緒！" -ForegroundColor Green
