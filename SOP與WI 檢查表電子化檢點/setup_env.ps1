# 一鍵環境設定腳本 - SOP / WI 檢查表電子化檢點系統
$ErrorActionPreference = "Continue"
Write-Host "=== SOP / WI 檢查表電子化檢點系統 - 環境檢測與安裝 ===" -ForegroundColor Cyan

# 1. Check Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Python: $(python --version)" -ForegroundColor Green
    python -m pip install --quiet pillow python-docx
} else {
    Write-Host "[WARN] 未偵測到 Python，請先安裝 Python 3.9+" -ForegroundColor Yellow
}

# 2. Check Node / Wrangler (for Cloudflare D1 track)
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Node/npm 已安裝" -ForegroundColor Green
    if (-not (Get-Command wrangler -ErrorAction SilentlyContinue)) {
        Write-Host "提示：如需部署 Cloudflare D1，可執行 npm install -g wrangler" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] wrangler CLI 已就緒" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] 未安裝 Node.js（僅部署 Cloudflare D1 時需要）" -ForegroundColor Gray
}

Write-Host "環境檢查完成！可雙擊 2_PWA_App版\啟動PWA本機測試.bat 立即啟動。" -ForegroundColor Green
