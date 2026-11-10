# =====================================================================
# 🚀 AI 圖片/PDF 雙重 OCR 轉 Excel 系統環境一鍵設定腳本 (setup_env.ps1)
# =====================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎨 開始檢查並安裝「AI 圖片/PDF 雙重 OCR 轉 Excel 系統」環境..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 檢查 Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✓ 偵測到 Python，開始檢查依賴套件..." -ForegroundColor Green
    
    $packages = @(
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "google-genai",
        "easyocr",
        "openpyxl",
        "python-multipart",
        "Pillow",
        "pymupdf",
        "opencv-python"
    )

    foreach ($pkg in $packages) {
        Write-Host "  -> 檢查套件: $pkg" -ForegroundColor Gray
        python -m pip install $pkg -q
    }

    # 確保暫存目錄存在
    $outputDir = Join-Path $PSScriptRoot "outputs"
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        Write-Host "✓ 建立輸出資料夾: $outputDir" -ForegroundColor Green
    }

    Write-Host "✓ 所有 Python 依賴安裝完成！" -ForegroundColor Green
} else {
    Write-Warning "⚠️ 未在系統中偵測到 Python，請先安裝 Python 3.9 以上！"
}
