# 企業活動簽到系統 - 一鍵環境檢測與設定腳本 (setup_env.ps1)
$ErrorActionPreference = "Continue"
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  企業活動簽到系統 - 環境檢測與初始化" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. 檢查 Python
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    Write-Host "[OK] 偵測到 Python: $(python --version)" -ForegroundColor Green
    # 檢查 python-docx (用於 build_manual_doc.py)
    python -c "import docx" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[安裝] 正在安裝 python-docx（供產出操作手冊使用）..." -ForegroundColor Yellow
        python -m pip install python-docx -q
    } else {
        Write-Host "[OK] python-docx 已就緒" -ForegroundColor Green
    }
} else {
    Write-Host "[提示] 未偵測到 Python（不影響雙擊 1_Web_網頁版\index.html 預覽，但 PWA 本機伺服器與手冊產生需 Python）" -ForegroundColor Yellow
}

# 2. 檢查 Node.js (未來上 Cloudflare D1 才需要)
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    Write-Host "[OK] 偵測到 Node.js: $(node --version)（未來可直接使用 Wrangler 部署 Cloudflare D1）" -ForegroundColor Green
} else {
    Write-Host "[資訊] 未偵測到 Node.js（目前給人資預覽無需安裝，未來要上雲端時再安裝即可）" -ForegroundColor Gray
}

Write-Host ""
Write-Host "初始化完成！可直接雙擊「點我預覽簽到系統(給人資看).bat」開啟系統。" -ForegroundColor Green
