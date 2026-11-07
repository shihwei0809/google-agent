# ============================================================
# setup_env.ps1 - 永豐 Shioaji 即時看盤儀表板一鍵環境安裝腳本
# ============================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  永豐 Shioaji 即時看盤儀表板 - 環境自動部署與安裝" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. 檢查 Python
Write-Host "`n[1/4] 檢查 Python 環境..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "  -> 找到 Python: $ver" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  [!] 找不到 Python，請先安裝 Python 3.9+ 並加入 PATH。" -ForegroundColor Red
    exit 1
}

# 2. 升級 pip
Write-Host "`n[2/4] 升級與確認 pip..." -ForegroundColor Yellow
try {
    & $pythonCmd -m pip install --upgrade pip -q
    Write-Host "  -> pip 就緒" -ForegroundColor Green
} catch {
    Write-Host "  -> pip 確認完畢 (略過升級)" -ForegroundColor Gray
}

# 3. 安裝核心 Web 與圖表服務依賴
Write-Host "`n[3/4] 安裝專案核心套件 (FastAPI, Uvicorn, WebSockets, etc.)..." -ForegroundColor Yellow
$reqFile = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $reqFile) {
    & $pythonCmd -m pip install -r $reqFile
    Write-Host "  -> 核心依賴安裝完成" -ForegroundColor Green
}

# 4. 檢查與嘗試安裝 shioaji 模組
Write-Host "`n[4/4] 檢查 Shioaji 永豐 API 套件..." -ForegroundColor Yellow
$shioajiCheck = & $pythonCmd -c "import shioaji; print(shioaji.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  -> 已安裝 Shioaji 版本: $shioajiCheck" -ForegroundColor Green
} else {
    Write-Host "  -> 正在嘗試安裝 shioaji (永豐金證券官方 Python SDK)..." -ForegroundColor Yellow
    try {
        & $pythonCmd -m pip install shioaji -q
        Write-Host "  -> Shioaji 安裝成功！" -ForegroundColor Green
    } catch {
        Write-Host "  [提示] Shioaji 安裝略過或失敗（可能因 Python 版本或網路限制）。" -ForegroundColor DarkYellow
        Write-Host "         不用擔心！本系統內建「高仿真即時模擬盤」，可在無 Shioaji 模組下直接看盤與體驗！" -ForegroundColor Cyan
    }
}

# 建立預設 .env
$envFile = Join-Path $PSScriptRoot ".env"
$envExFile = Join-Path $PSScriptRoot ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExFile)) {
    Copy-Item $envExFile $envFile
    Write-Host "`n  -> 已自動由 .env.example 建立預設 .env 設定檔" -ForegroundColor Green
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  環境初始化完成！" -ForegroundColor Green
Write-Host "  現在您可以直接雙擊執行 [啟動看盤儀表板.bat] 開啟系統！" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
