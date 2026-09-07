# 勝一出貨排程管理系統 - 一鍵環境配置腳本
Write-Host ========================================= -ForegroundColor Cyan
Write-Host  正在檢測並配置勝一出貨排程管理系統環境... -ForegroundColor Cyan
Write-Host ========================================= -ForegroundColor Cyan

# 1. 檢測 Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host [X] 未偵測到 Node.js，請先安裝 Node.js 18+。 -ForegroundColor Red
    exit 1
}
Write-Host [V] 偵測到 Node.js，正在安裝 npm 依賴套件... -ForegroundColor Green
npm install

# 2. 檢測 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host [!] 未偵測到 Python，建議安裝 Python 3.10+ 以支援條碼生成與手冊產出。 -ForegroundColor Yellow
} else {
    Write-Host [V] 偵測到 Python，正在確認 openpyxl, qrcode, pillow, python-docx, pywin32... -ForegroundColor Green
    python -m pip install --quiet openpyxl qrcode pillow python-docx pywin32
}

Write-Host ========================================= -ForegroundColor Green
Write-Host [V] 環境配置就緒！ -ForegroundColor Green
Write-Host  - 執行 一鍵啟動系統.bat 可立即啟動本機伺服器 -ForegroundColor Green
Write-Host  - 執行 python build_manual_doc.py 可產出操作手冊 Word 與 PDF -ForegroundColor Green
Write-Host ========================================= -ForegroundColor Green
