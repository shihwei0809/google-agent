# ============================================================
# 🌐 全域開發環境一鍵安裝腳本 (電腦上只需執行一次)
# 全域環境一鍵安裝.ps1
#
# 安裝內容:
#   ① Python 3.12 (含 pip)
#   ② Git
#   ③ 所有 AI 專案共用的 pip 套件
#
# 使用方式:
#   右鍵 → 以系統管理員身份執行 PowerShell
#   或直接雙擊「全域環境一鍵安裝.bat」
# ============================================================

# 要求管理員權限
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host ""
    Write-Host "  ⚠ 需要管理員權限！正在以系統管理員重新啟動..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   🌐 AI 專案全域環境一鍵安裝 (電腦僅需執行一次)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  本腳本將自動安裝以下內容：" -ForegroundColor White
Write-Host "   ① Python 3.12 (程式執行引擎)" -ForegroundColor Gray
Write-Host "   ② Git (版本控制工具)" -ForegroundColor Gray
Write-Host "   ③ 所有 AI 系統共用的 Python 套件" -ForegroundColor Gray
Write-Host ""
Write-Host "  安裝過程需要 5~15 分鐘，請保持網路連線" -ForegroundColor Gray
Write-Host ""
Read-Host "  按 Enter 開始安裝..."

function Write-Step($msg) { Write-Host "`n  ▶ $msg" -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host "  ✔ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Magenta }
function Write-Info($msg) { Write-Host "  ℹ $msg" -ForegroundColor Cyan }

# ============================================================
# STEP 1 - 確認 winget 可用 (Windows 10/11 內建)
# ============================================================
Write-Step "STEP 1/4 - 確認安裝工具 (winget)..."
$wingetAvailable = $false
try {
    $wingetVer = winget --version 2>&1
    if ($wingetVer -match "v\d") {
        Write-OK "winget 可用: $wingetVer"
        $wingetAvailable = $true
    }
} catch {}

if (-not $wingetAvailable) {
    Write-Warn "winget 不可用，將改用直接下載方式安裝 Python"
}

# ============================================================
# STEP 2 - 安裝 Python 3.12
# ============================================================
Write-Step "STEP 2/4 - 偵測 / 安裝 Python..."

$pythonOK = $false
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            if ([int]$Matches[1] -ge 3 -and [int]$Matches[2] -ge 9) {
                Write-OK "Python 已安裝: $ver"
                $pythonOK = $true
                $global:pythonCmd = $cmd
                break
            }
        }
    } catch {}
}

if (-not $pythonOK) {
    Write-Info "Python 未安裝，開始自動安裝..."

    if ($wingetAvailable) {
        Write-Info "使用 winget 安裝 Python 3.12..."
        winget install --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
    } else {
        # 直接下載官方安裝檔
        Write-Info "直接下載 Python 3.12 官方安裝程式..."
        $pyInstaller = "$env:TEMP\python_installer.exe"
        $pyUrl = "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
        Write-Info "下載中 (約 27MB)..."
        try {
            Invoke-WebRequest -Uri $pyUrl -OutFile $pyInstaller -UseBasicParsing
            Write-Info "安裝中 (靜默安裝，請稍候)..."
            Start-Process -FilePath $pyInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
            Remove-Item $pyInstaller -Force
            Write-OK "Python 安裝完成"
        } catch {
            Write-Host "  ✘ 自動下載失敗，請手動前往安裝：" -ForegroundColor Red
            Write-Host "    https://www.python.org/downloads/" -ForegroundColor Cyan
            Write-Host "    安裝時請勾選 [Add Python to PATH]" -ForegroundColor White
        }
    }

    # 重新整理 PATH 後重新偵測
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python 3") {
                Write-OK "Python 安裝確認: $ver"
                $global:pythonCmd = $cmd
                $pythonOK = $true
                break
            }
        } catch {}
    }

    if (-not $pythonOK) {
        Write-Host ""
        Write-Host "  ⚠ Python 安裝後需要重新開機才能生效" -ForegroundColor Magenta
        Write-Host "  請重新開機後再次執行本腳本完成套件安裝" -ForegroundColor White
        Write-Host ""
        Read-Host "  按 Enter 離開..."
        exit 0
    }
}

# ============================================================
# STEP 3 - 安裝 Git (選用，但強烈建議)
# ============================================================
Write-Step "STEP 3/4 - 偵測 / 安裝 Git..."
$gitOK = $false
try {
    $gitVer = git --version 2>&1
    if ($gitVer -match "git version") {
        Write-OK "Git 已安裝: $gitVer"
        $gitOK = $true
    }
} catch {}

if (-not $gitOK) {
    Write-Info "Git 未安裝，開始自動安裝..."
    if ($wingetAvailable) {
        winget install --id Git.Git --silent --accept-source-agreements --accept-package-agreements
        Write-OK "Git 安裝完成"
    } else {
        Write-Warn "請手動安裝 Git: https://git-scm.com/download/win"
    }
}

# ============================================================
# STEP 4 - 安裝所有 AI 專案共用的 pip 套件 (全域)
# ============================================================
Write-Step "STEP 4/4 - 安裝 AI 專案共用 Python 套件..."
Write-Info "使用的 Python: $($global:pythonCmd)"
Write-Host ""

# 先升級 pip 本身
& $global:pythonCmd -m pip install --upgrade pip -q
Write-OK "pip 已更新至最新版"

# 所有 AI 專案共用套件清單
$globalPackages = @(
    # Web 框架
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0",
    "python-multipart>=0.0.6",

    # AI / Gemini
    "google-genai",

    # 資料驗證
    "pydantic>=2.0.0",

    # Excel / Word 文件
    "openpyxl>=3.1.0",
    "python-docx>=1.1.0",
    "XlsxWriter",

    # 網頁爬蟲 (104爬蟲等需要)
    "requests>=2.31.0",
    "beautifulsoup4",
    "lxml",

    # 通用工具
    "python-dotenv",
    "aiofiles"
)

Write-Info "共 $($globalPackages.Count) 個套件，逐一安裝中..."
Write-Host ""

$installed = 0
$failed = @()

foreach ($pkg in $globalPackages) {
    $pkgName = ($pkg -split ">=|<=|==")[0].Trim()
    $checkName = $pkgName.Replace("-", "_").Replace(".", "_").ToLower()

    # 套件 import 名稱特殊對照
    $importMap = @{
        "fastapi"           = "fastapi"
        "uvicorn"           = "uvicorn"
        "python_multipart"  = "multipart"
        "google_genai"      = "google.genai"
        "pydantic"          = "pydantic"
        "openpyxl"          = "openpyxl"
        "python_docx"       = "docx"
        "xlsxwriter"        = "xlsxwriter"
        "requests"          = "requests"
        "beautifulsoup4"    = "bs4"
        "lxml"              = "lxml"
        "python_dotenv"     = "dotenv"
        "aiofiles"          = "aiofiles"
    }

    $importName = if ($importMap.ContainsKey($checkName)) { $importMap[$checkName] } else { $checkName }
    $testResult = & $global:pythonCmd -c "import $importName; print('ok')" 2>&1

    if ("$testResult".Trim() -eq "ok") {
        Write-OK "$pkgName 已存在"
    } else {
        try {
            & $global:pythonCmd -m pip install $pkg -q
            Write-OK "$pkgName 安裝成功"
            $installed++
        } catch {
            Write-Warn "$pkgName 安裝失敗，可手動補裝"
            $failed += $pkgName
        }
    }
}

# ============================================================
# 完成摘要
# ============================================================
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "   ✅ 全域環境安裝完成！" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  安裝摘要:" -ForegroundColor White

$pyVer = & $global:pythonCmd --version 2>&1
Write-Host "   Python  : $pyVer" -ForegroundColor Cyan
try {
    $gitVer2 = git --version 2>&1
    Write-Host "   Git     : $gitVer2" -ForegroundColor Cyan
} catch {}
Write-Host "   新安裝套件: $installed 個" -ForegroundColor Cyan
if ($failed.Count -gt 0) {
    Write-Host "   安裝失敗 : $($failed -join ', ')" -ForegroundColor Magenta
}

Write-Host ""
Write-Host "  ✅ 往後所有 AI 系統，雙擊各自的 .bat 啟動即可！" -ForegroundColor Green
Write-Host "  ✅ 不再需要手動安裝 Python 或套件。" -ForegroundColor Green
Write-Host ""
Read-Host "  按 Enter 完成..."
