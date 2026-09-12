# setup_env.ps1 - 一鍵安裝/環境設定腳本
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "正在檢查與配置 台積電槽車三合一單架機伺服器 環境..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. 檢查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[X] 未偵測到 Python，請先安裝 Python 3.8+！" -ForegroundColor Red
    Exit 1
}

# 2. 安裝必要套件
 = @("fastapi", "uvicorn", "openpyxl", "qrcode", "pillow")
Write-Host "[*] 正在安裝必要套件: ..." -ForegroundColor Yellow

python -m pip install --upgrade pip --quiet
python -m pip install  --quiet

Write-Host "[V] 環境配置完成！可執行 'python server.py' 或雙擊 '架設伺服器_一鍵啟動.bat' 啟動服務。" -ForegroundColor Green
