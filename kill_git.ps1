# kill_git.ps1
# 一鍵深層清除卡死 Git 進程、解除鎖定並釋放 CPU

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  [一鍵深層清除卡死 Git 進程與釋放 CPU 工具]" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 檢查目前 git.exe 數量
$beforeCount = (Get-Process git -ErrorAction SilentlyContinue).Count
if ($beforeCount -gt 0) {
    Write-Host "[1/3] 正在檢查目前執行的 git.exe 數量: $beforeCount" -ForegroundColor Red
} else {
    Write-Host "[1/3] 正在檢查目前執行的 git.exe 數量: 0" -ForegroundColor Green
}

# 2. 透過 WMI 核心層深度強制終止（重複兩次確認清除徹底）
Write-Host "[2/3] 正在執行 WMI 核心層深層強制清除..." -ForegroundColor Yellow
$totalKilled = 0
for ($attempt = 1; $attempt -le 3; $attempt++) {
    $procs = Get-WmiObject Win32_Process -Filter "Name = 'git.exe'"
    if (-not $procs) { break }
    foreach ($p in $procs) {
        $null = $p.Terminate()
        $totalKilled++
    }
    Start-Sleep -Milliseconds 300
}

# 輔助 taskkill 二度確保
Stop-Process -Name git -Force -ErrorAction SilentlyContinue
if ($totalKilled -gt 0) {
    Write-Host "      [OK] 已透過 WMI 核心層累計終結 $totalKilled 個 git.exe 進程！" -ForegroundColor Green
} else {
    Write-Host "      [OK] 目前沒有卡死的 git.exe 進程。" -ForegroundColor Green
}

# 3. 清理 .git 鎖定檔（防止日後 git 指令報錯）
Write-Host "[3/3] 檢查並清理殘留的 .git 鎖定檔..." -ForegroundColor Yellow
$locks = Get-ChildItem -Path "D:\GOOGLE ANGET" -Recurse -Filter "*.lock" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "\\.git\\" }
if ($locks) {
    foreach ($l in $locks) {
        Remove-Item $l.FullName -Force -ErrorAction SilentlyContinue
        Write-Host "      [CLEAN] 已清除鎖定檔: $($l.FullName)" -ForegroundColor Yellow
    }
}

$gcPid = "D:\GOOGLE ANGET\.git\gc.pid"
if (Test-Path $gcPid) {
    Remove-Item $gcPid -Force -ErrorAction SilentlyContinue
    Write-Host "      [CLEAN] 已清除殘留的 gc.pid！" -ForegroundColor Yellow
}
Write-Host "      [OK] 鎖定檔檢查與清理完畢。" -ForegroundColor Green

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  檢查清理結果：" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Start-Sleep -Milliseconds 500
$remaining = (Get-Process git -ErrorAction SilentlyContinue).Count
if ($remaining -eq 0) {
    Write-Host "  [OK] 剩餘 git.exe: 0 (全部乾淨清除)" -ForegroundColor Green
} else {
    Write-Host "  [ALERT] 剩餘 git.exe: $remaining" -ForegroundColor Red
}

$cpu = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
Write-Host "  [CPU] 當前系統總 CPU 使用率: $([Math]::Round($cpu, 1))%" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""