Write-Host "========================================" -ForegroundColor Cyan
Write-Host " AI 影音自動剪輯工作站 環境安裝" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

python -m pip install --upgrade pip
python -m pip install -r "$PSScriptRoot\requirements.txt"

Write-Host "`n[✓] 安裝完成！可直接執行 '啟動AI影音剪輯工作站.bat' 啟動服務。" -ForegroundColor Green
