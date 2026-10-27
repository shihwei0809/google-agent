# ========================================================
# N系列報表輸出系統 (勝一專用版) - 一鍵環境設定與相依套件安裝腳本
# ========================================================

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   N系列報表輸出系統 (勝一專用版) - 環境配置精靈        " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 檢查 Python
Write-Host "[1/3] 檢查 Python 安裝狀態..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "  ✅ 找到 Python: $ver" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  ❌ 未偵測到 Python！請先安裝 Python 3.9 以上版本。" -ForegroundColor Red
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# 2. 檢查並升級 pip
Write-Host ""
Write-Host "[2/3] 檢查 pip 套件管理器..." -ForegroundColor Yellow
& $pythonCmd -m pip --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠️ pip 異常，嘗試修復中..." -ForegroundColor Red
    & $pythonCmd -m ensurepip --default-pip
}

# 3. 檢查並安裝必要套件
Write-Host ""
Write-Host "[3/3] 檢查並安裝必要相依套件..." -ForegroundColor Yellow
$packages = @(
    @{ Import = "openpyxl"; Pip = "openpyxl" },
    @{ Import = "PIL"; Pip = "Pillow" },
    @{ Import = "qrcode"; Pip = "qrcode" },
    @{ Import = "pytesseract"; Pip = "pytesseract" },
    @{ Import = "docx"; Pip = "python-docx" }
)

foreach ($pkg in $packages) {
    $importName = $pkg.Import
    $pipName = $pkg.Pip
    & $pythonCmd -c "import $importName" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  📦 安裝套件: $pipName ..." -ForegroundColor Yellow
        & $pythonCmd -m pip install $pipName
    } else {
        Write-Host "  ✅ $pipName 已就緒" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  🎉 勝一專用版環境設定完成！隨時可執行 啟動本機視窗版.bat  " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
