# ==============================================================================
# 自動清理卡死/孤兒 Git 進程腳本 (Clean Stuck Git Processes)
# 用途: 每天早上 07:30 定時執行，或平時手動執行，解決 git.exe 死循環佔滿 CPU 100% 問題
# ==============================================================================

param(
    [switch]$ForceAll = $true # 預設強制清理所有背景殘留 git
)

$logPath = "d:\GOOGLE ANGET\scripts\clean_git.log"
$logDir = Split-Path $logPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$killedCount = 0

Add-Content -Path $logPath -Value "[$now] === 開始檢查卡死 Git 程序 ==="

try {
    $gitProcesses = Get-Process -Name git -ErrorAction SilentlyContinue

    if ($gitProcesses) {
        foreach ($proc in $gitProcesses) {
            $shouldKill = $false
            $runtime = [datetime]::Now - $proc.StartTime

            if ($ForceAll) {
                $shouldKill = $true
            } elseif ($runtime.TotalMinutes -ge 2) {
                # 運行超過 2 分鐘視為掛起
                $shouldKill = $true
            }

            if ($shouldKill) {
                try {
                    $pidToKill = $proc.Id
                    $cpuTime = $proc.CPU
                    $runtimeStr = "{0:N1} 分鐘" -f $runtime.TotalMinutes
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                    $killedCount++
                    Add-Content -Path $logPath -Value "[$now] 成功終止卡死進程: PID $pidToKill (已運行 $runtimeStr, 消耗 CPU: $cpuTime 秒)"
                } catch {
                    Add-Content -Path $logPath -Value "[$now] 終止進程 PID $($proc.Id) 失敗: $_"
                }
            }
        }
    } else {
        Add-Content -Path $logPath -Value "[$now] 系統目前無殘留的 Git 進程，運行正常。"
    }

    # 檢查並清除 d:\GOOGLE ANGET 根目錄的殘留 index.lock
    $lockFiles = @(
        "d:\GOOGLE ANGET\.git\index.lock",
        "d:\GOOGLE ANGET\my-ai-brain\.git\index.lock"
    )
    foreach ($lock in $lockFiles) {
        if (Test-Path $lock) {
            Remove-Item -Path $lock -Force -ErrorAction SilentlyContinue
            Add-Content -Path $logPath -Value "[$now] 偵測並已移除殘留鎖定檔: $lock"
        }
    }

    Add-Content -Path $logPath -Value "[$now] === 檢查完畢，共清理 $killedCount 個卡死進程 ===`r`n"
} catch {
    Add-Content -Path $logPath -Value "[$now] 發生錯誤: $_`r`n"
}
