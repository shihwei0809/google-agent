# 台積三合一單與 COA 雙重核對系統 - 一鍵環境配置腳本
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " 正在檢測並配置手冊生成環境 (Python Docx)..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 檢測 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[X] 未偵測到 Python，請先安裝 Python 3.10+。" -ForegroundColor Red
    exit 1
}

Write-Host "[V] 偵測到 Python，正在安裝/確認依賴套件..." -ForegroundColor Green
pip install --upgrade python-docx pywin32 -q

Write-Host "[V] 環境配置完成！執行 python build_manual_doc.py 可立即產出手冊。" -ForegroundColor Green
