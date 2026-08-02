# 一鍵環境與測試腳本
Write-Host "🚀 正在測試 [軟管對刷-T100QC串接中間件備案] 環境..." -ForegroundColor Green

if (Get-Command php -ErrorAction SilentlyContinue) {
    Write-Host "✅ 偵測到 PHP 環境，正在語法檢查..." -ForegroundColor Cyan
    php -l "$PSScriptRoot\t100_qc_middleware.php"
} else {
    Write-Host "⚠️ 本機未安裝 PHP CLI，請使用 XAMPP 或 PHP 執行檔。" -ForegroundColor Yellow
}

Write-Host "完成。" -ForegroundColor Green
