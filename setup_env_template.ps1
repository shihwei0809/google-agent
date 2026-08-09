# ============================================================
# 🤖 [專案名稱] - 一鍵環境自動偵測與安裝腳本
# setup_env.ps1  (通用標準模板 v2.0)
#
# 使用方式：
#   1. 複製本檔案到專案根目錄
#   2. 修改 [A] 區段的專案名稱與套件清單
#   3. 修改 [B] 區段的必要資料夾清單
#   4. 若非 Python 專案，移除 STEP 1~3，加入對應的環境檢查
# ============================================================
$ErrorActionPreference = "Stop"

# ============================================================
# [A] 🔧 請依專案需求修改此區段
# ============================================================
$PROJECT_NAME  = "專案系統名稱"          # 顯示用的系統名稱
$DEFAULT_PORT  = 8000                     # 預設 Port
$ENTRY_COMMAND = "python -m uvicorn main:app --host 0.0.0.0 --port"  # 啟動指令

# Python 套件清單 (name=顯示名, import=Python import 名, pip=pip install 名)
$REQUIRED_PACKAGES = @(
    @{ name="fastapi";          import="fastapi";      pip="fastapi>=0.100.0"  },
    @{ name="uvicorn";          import="uvicorn";      pip="uvicorn>=0.22.0"   },
    @{ name="google-genai";     import="google.genai"; pip="google-genai"      },
    @{ name="pydantic";         import="pydantic";     pip="pydantic>=2.0.0"   },
    @{ name="python-multipart"; import="multipart";    pip="python-multipart"  },
    @{ name="openpyxl";         import="openpyxl";     pip="openpyxl"          },
    @{ name="python-docx";      import="docx";         pip="python-docx"       }
    # 範例: @{ name="requests"; import="requests"; pip="requests" },
)

# ============================================================
# [B] 🗂️ 專案必要資料夾 (不存在時自動建立)
# ============================================================
$REQUIRED_FOLDERS = @(
    "data",
    "data\audios",
    "static"
)

# 必要的初始化空檔案 (路徑 -> 預設內容)
$REQUIRED_FILES = @{
    "data\db.json" = "[]"
}

# ============================================================
# 以下為通用執行邏輯，一般不需要修改
# ============================================================

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  $PROJECT_NAME - 環境自動偵測與啟動" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

function Write-Step($msg) { Write-Host "  ▶ $msg" -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host "  ✔ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Magenta }
function Write-Fail($msg) { Write-Host "  ✘ $msg" -ForegroundColor Red }

# ---- STEP 1: 偵測 Python ----
Write-Step "STEP 1/5 - 偵測 Python 3.9+ 環境..."
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            if ([int]$Matches[1] -ge 3 -and [int]$Matches[2] -ge 9) {
                $pythonCmd = $cmd
                Write-OK "Python 已就緒: $ver  (指令: $cmd)"
                break
            } else {
                Write-Warn "Python 版本過舊 ($ver)，需要 3.9+"
            }
        }
    } catch { continue }
}

if (-not $pythonCmd) {
    Write-Fail "未偵測到 Python 3.9+！"
    Write-Host ""
    Write-Host "  請至 https://www.python.org/downloads/ 下載安裝" -ForegroundColor White
    Write-Host "  安裝時請勾選 [Add Python to PATH]" -ForegroundColor White
    Write-Host ""
    $ans = Read-Host "  是否立即開啟 Python 下載頁？(Y/N)"
    if ($ans -eq "Y") { Start-Process "https://www.python.org/downloads/" }
    exit 1
}

# ---- STEP 2: 確認 pip ----
Write-Step "STEP 2/5 - 確認 pip 套件管理器..."
try {
    $pipVer = & $pythonCmd -m pip --version 2>&1
    Write-OK "pip 正常: $pipVer"
} catch {
    Write-Warn "pip 未安裝，正在修復..."
    & $pythonCmd -m ensurepip --upgrade
    & $pythonCmd -m pip install --upgrade pip -q
    Write-OK "pip 修復完成"
}

# ---- STEP 3: 套件檢查與自動安裝 ----
Write-Step "STEP 3/5 - 套件環境檢查..."
$toInstall = @()
foreach ($pkg in $REQUIRED_PACKAGES) {
    $result = & $pythonCmd -c "import $($pkg.import); print('ok')" 2>&1
    if ("$result".Trim() -eq "ok") {
        Write-OK "$($pkg.name) 已安裝"
    } else {
        Write-Warn "$($pkg.name) 未安裝，加入待安裝清單"
        $toInstall += $pkg.pip
    }
}

if ($toInstall.Count -gt 0) {
    Write-Host ""
    Write-Step "正在安裝缺少套件: $($toInstall -join ', ')"
    Write-Host "  (此步驟需要網路連線，請耐心等待...)" -ForegroundColor Gray
    try {
        & $pythonCmd -m pip install @toInstall -q
        Write-OK "套件安裝完成！"
    } catch {
        Write-Fail "套件安裝失敗！"
        Write-Host ""
        Write-Host "  請手動執行以下指令後重試：" -ForegroundColor White
        Write-Host "  $pythonCmd -m pip install $($toInstall -join ' ')" -ForegroundColor Cyan
        Write-Host ""
        Read-Host "  按 Enter 離開..."
        exit 1
    }
} else {
    Write-OK "所有套件皆已就緒！"
}

# ---- STEP 4: 資料夾與初始檔案 ----
Write-Step "STEP 4/5 - 確認資料夾結構..."
foreach ($folder in $REQUIRED_FOLDERS) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-OK "建立資料夾: $folder"
    }
}
foreach ($filePath in $REQUIRED_FILES.Keys) {
    if (-not (Test-Path $filePath)) {
        $REQUIRED_FILES[$filePath] | Out-File -FilePath $filePath -Encoding utf8
        Write-OK "建立初始檔案: $filePath"
    }
}
Write-OK "資料夾結構正常"

# ---- STEP 5: 找可用 Port ----
Write-Step "STEP 5/5 - 搜尋可用 Port..."
$port = $DEFAULT_PORT
for ($p = $DEFAULT_PORT; $p -le ($DEFAULT_PORT + 50); $p++) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $p)
        $listener.Start()
        $listener.Stop()
        $port = $p
        break
    } catch { continue }
}
if ($port -ne $DEFAULT_PORT) {
    Write-Warn "預設 Port $DEFAULT_PORT 已被佔用，自動切換至: Port $port"
} else {
    Write-OK "使用 Port: $port"
}

# ---- 取得本機 IP ----
$localIP = "127.0.0.1"
try {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } |
        Select-Object -First 1).IPAddress
} catch {}

# ---- 啟動 ----
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  環境檢查全部通過！正在啟動 $PROJECT_NAME..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  本機存取:  http://localhost:$port" -ForegroundColor Cyan
Write-Host "  區網存取:  http://$($localIP):$port  (提供給同事使用)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  按 Ctrl+C 可停止服務" -ForegroundColor Gray
Write-Host ""

# 延遲 2 秒後自動開啟瀏覽器
Start-Job -ScriptBlock {
    param($p)
    Start-Sleep 2
    Start-Process "http://localhost:$p"
} -ArgumentList $port | Out-Null

# 啟動服務
Invoke-Expression "$ENTRY_COMMAND $port"
