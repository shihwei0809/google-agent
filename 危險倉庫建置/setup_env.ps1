# 環境設定腳本 - 化學品防爆倉儲專案
Write-Host "開始初始化專案環境..." -ForegroundColor Cyan

# 檢查是否有 Python 環境 (為未來模擬工具做準備)
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    Write-Host "Python 已安裝，版本資訊：" -ForegroundColor Green
    python --version
} else {
    Write-Host "尚未安裝 Python，建議未來若需執行模擬工具請先安裝 Python。" -ForegroundColor Yellow
}

Write-Host "本專案目前以文件報告為主，無特殊依賴套件需強制安裝。" -ForegroundColor Green
Write-Host "環境初始化完成！請查閱 README.md 及報告內容。" -ForegroundColor Cyan
