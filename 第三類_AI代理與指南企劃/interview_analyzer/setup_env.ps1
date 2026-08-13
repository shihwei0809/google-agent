Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " [Setup] Initializing Interview AI System..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

function Get-RealPythonPath {
    $candidates = [System.Collections.Generic.List[string]]::new()

    # Check py launcher first
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { $candidates.Add($pyCmd.Source) }

    # Check python in PATH
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { $candidates.Add($pythonCmd.Source) }

    # Check standard install locations
    $commonPaths = @(
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Program Files\Python313\python.exe",
        "C:\Program Files\Python312\python.exe"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) { $candidates.Add($p) }
    }

    foreach ($cand in $candidates) {
        if ($cand -like "*WindowsApps*") { continue }
        try {
            $ver = & $cand --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") {
                return $cand
            }
        } catch {}
    }
    return $null
}

$realPython = Get-RealPythonPath

if (-not $realPython) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Yellow
    Write-Host " [System] 未偵測到 Python，正在啟動一鍵自動背景安裝程序..." -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Yellow

    $installedSuccess = $false

    # Attempt 1: winget
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetCmd) {
        Write-Host "[Info] 正在使用 Windows Package Manager (winget) 背景安裝 Python 3.12..." -ForegroundColor Cyan
        try {
            $p = Start-Process winget -ArgumentList "install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent" -Wait -PassThru -NoNewWindow
            if ($p.ExitCode -eq 0) { $installedSuccess = $true }
        } catch {}
    }

    # Attempt 2: Direct Official Installer Download & Quiet Install
    if (-not $installedSuccess) {
        Write-Host "[Info] 正在下載 Python 3.12 官方靜默安裝檔..." -ForegroundColor Cyan
        $url = "https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe"
        $tempExe = "$env:TEMP\python-3.12.2-amd64.exe"
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $tempExe -UseBasicParsing
            Write-Host "[Info] 正在執行背景靜默安裝並自動設定 PATH (請稍候)..." -ForegroundColor Cyan
            $p = Start-Process -FilePath $tempExe -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait -PassThru
            Remove-Item $tempExe -ErrorAction SilentlyContinue
            if ($p.ExitCode -eq 0) { $installedSuccess = $true }
        } catch {
            Write-Host "[Warning] 自動下載安裝時發生例外: $_" -ForegroundColor Yellow
        }
    }

    # Refresh PATH environment variable in current PowerShell session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    # Re-check Python
    $realPython = Get-RealPythonPath

    if (-not $realPython) {
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Red
        Write-Host " [提示] 自動安裝需要重新啟動視窗，或請開啟官方網站安裝：" -ForegroundColor Red
        Write-Host " (網址: https://www.python.org/downloads/)" -ForegroundColor White
        Write-Host " 安裝時請務必勾選 【Add python.exe to PATH】！" -ForegroundColor Red
        Write-Host "==========================================================" -ForegroundColor Red
        try { Start-Process "https://www.python.org/downloads/" } catch {}
        pause
        exit 1
    }
}

Write-Host "[OK] Real Python found: $realPython" -ForegroundColor Green

# If .venv exists but is invalid for this machine, remove it first
if (Test-Path ".venv") {
    try {
        $testRes = & .\.venv\Scripts\python.exe --version 2>&1
        if ($LASTEXITCODE -ne 0 -or $testRes -notmatch "Python") {
            Write-Host "[Warning] 檢測到舊的或非本機的 .venv 環境，正在自動清理重建..." -ForegroundColor Yellow
            Remove-Item ".venv" -Recurse -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Remove-Item ".venv" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Create venv if not exists
if (-Not (Test-Path ".venv")) {
    Write-Host "[Info] Creating virtual environment .venv ..." -ForegroundColor Yellow
    & $realPython -m venv .venv
}

if (-Not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "[Error] Virtual environment creation failed! Retrying..." -ForegroundColor Red
    & $realPython -m venv .venv
}

# Upgrade pip
Write-Host "[Info] Upgrading pip..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip -q

# Install requirements
Write-Host "[Info] Installing packages from requirements.txt ..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host " [Success] Setup complete! Starting server..." -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
