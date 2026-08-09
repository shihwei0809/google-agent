# ============================================================
# 🤖 AI 面試語音分析系統 - 一鍵環境自動偵測與安裝腳本
# setup_env.ps1
# 版本: v2.0 | 支援: Windows 10/11 PowerShell 5+
# ============================================================
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  AI 面試語音分析系統 - 環境自動偵測與啟動程式" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# ---- 工具函式 ----
function Write-Step($msg) { Write-Host "  ▶ $msg" -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host "  ✔ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Magenta }
function Write-Fail($msg) { Write-Host "  ✘ $msg" -ForegroundColor Red }

# ============================================================
# STEP 1 - 檢查 Python 是否安裝
# ============================================================
Write-Step "檢查 Python 環境..."
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+\.\d+)") {
            $major = [int]$Matches[1].Split(".")[0]
            $minor = [int]$Matches[1].Split(".")[1]
            if ($major -ge 3 -and $minor -ge 9) {
                $pythonCmd = $cmd
                Write-OK "找到 Python: $ver (指令: $cmd)"
                break
            } else {
                Write-Warn "找到 Python 但版本過舊 ($ver)，需要 3.9+"
            }
        }
    } catch { continue }
}

if (-not $pythonCmd) {
    Write-Fail "未偵測到 Python 3.9+！"
    Write-Host ""
    Write-Host "  請前往以下網址下載安裝 Python:" -ForegroundColor White
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  安裝時請勾選 [Add Python to PATH]，完成後重新執行此腳本。" -ForegroundColor White
    Write-Host ""
    Read-Host "  按 Enter 開啟 Python 下載頁面後離開..."
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# ============================================================
# STEP 2 - 檢查 pip 是否可用
# ============================================================
Write-Step "檢查 pip 套件管理器..."
try {
    $pipVer = & $pythonCmd -m pip --version 2>&1
    Write-OK "pip 正常: $pipVer"
} catch {
    Write-Warn "pip 未安裝，正在嘗試自動修復..."
    & $pythonCmd -m ensurepip --upgrade
    & $pythonCmd -m pip install --upgrade pip
    Write-OK "pip 修復完成"
}

# ============================================================
# STEP 3 - 檢查並安裝所需 Python 套件
# ============================================================
Write-Step "檢查並安裝必要套件 (依 requirements.txt)..."

# 必要套件清單
$requiredPackages = @(
    @{ name="fastapi";           import="fastapi";           pip="fastapi>=0.100.0"    },
    @{ name="uvicorn";           import="uvicorn";           pip="uvicorn>=0.22.0"     },
    @{ name="google-genai";      import="google.genai";      pip="google-genai"        },
    @{ name="pydantic";          import="pydantic";          pip="pydantic>=2.0.0"     },
    @{ name="python-multipart";  import="multipart";         pip="python-multipart"    },
    @{ name="openpyxl";          import="openpyxl";          pip="openpyxl"            },
    @{ name="python-docx";       import="docx";              pip="python-docx"         }
)

$toInstall = @()
foreach ($pkg in $requiredPackages) {
    $checkResult = & $pythonCmd -c "import $($pkg.import); print('ok')" 2>&1
    if ($checkResult -eq "ok") {
        Write-OK "$($pkg.name) 已安裝"
    } else {
        Write-Warn "$($pkg.name) 未安裝，加入安裝清單..."
        $toInstall += $pkg.pip
    }
}

if ($toInstall.Count -gt 0) {
    Write-Host ""
    Write-Step "正在安裝缺少的套件: $($toInstall -join ', ')"
    try {
        & $pythonCmd -m pip install --upgrade @toInstall -q
        Write-OK "套件安裝完成！"
    } catch {
        Write-Fail "套件安裝失敗，請檢查網路連線或手動執行:"
        Write-Host "  $pythonCmd -m pip install $($toInstall -join ' ')" -ForegroundColor White
        Read-Host "  按 Enter 離開..."
        exit 1
    }
} else {
    Write-OK "所有套件皆已安裝齊全！"
}

# ============================================================
# STEP 4 - 確認 data 資料夾與 db.json 存在
# ============================================================
Write-Step "確認資料夾結構..."
$foldersNeeded = @("data", "data\audios", "static")
foreach ($folder in $foldersNeeded) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-OK "建立資料夾: $folder"
    }
}
if (-not (Test-Path "data\db.json")) {
    "[]" | Out-File -FilePath "data\db.json" -Encoding utf8
    Write-OK "建立初始資料庫: data\db.json"
}
Write-OK "資料夾結構正常"

# ============================================================
# STEP 5 - 自動尋找可用 Port（避免 Port 衝突）
# ============================================================
Write-Step "搜尋可用 Port..."
$port = 8000
for ($p = 8000; $p -le 8050; $p++) {
    $test = Test-NetConnection -ComputerName localhost -Port $p -WarningAction SilentlyContinue -InformationLevel Quiet 2>$null
    if (-not $test) {
        $port = $p
        break
    }
}
Write-OK "使用 Port: $port"

# ============================================================
# STEP 6 - 取得本機 IP
# ============================================================
$localIP = "127.0.0.1"
try {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*"
    } | Select-Object -First 1).IPAddress
} catch {}

# ============================================================
# STEP 7 - 啟動服務
# ============================================================
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  環境檢查完成，正在啟動 AI 面試分析系統..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  本機存取:  http://localhost:$port" -ForegroundColor Cyan
Write-Host "  區網存取:  http://$($localIP):$port" -ForegroundColor Cyan
Write-Host ""
Write-Host "  (啟動後請在瀏覽器開啟上方網址，按 Ctrl+C 可停止服務)" -ForegroundColor Gray
Write-Host ""

# 自動開啟瀏覽器 (延遲 2 秒等服務啟動)
Start-Job -ScriptBlock {
    param($p)
    Start-Sleep 2
    Start-Process "http://localhost:$p"
} -ArgumentList $port | Out-Null

& $pythonCmd -m uvicorn main:app --host 0.0.0.0 --port $port
