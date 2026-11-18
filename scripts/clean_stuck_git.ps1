# ==============================================================================
# 自動清理卡死/孤兒 Git 進程腳本 (Clean Stuck Git Processes)
# 核心機制: 採用 .NET [System.Diagnostics.Process]::Kill() 底層 API，確保 100% 強制終止
# ==============================================================================

param(
    [switch]$ForceAll = $false # 若為 $true 則終止所有 git.exe；若為 $false 則終止運行超過 2 分鐘的進程
)

$logPath = "d:\GOOGLE ANGET\scripts\clean_git.log"
$logDir = Split-Path $logPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$killedCount = 0
$failCount = 0

Add-Content -Path $logPath -Value "[$now] === 開始掃描卡死 Git 進程 ==="

try {
    $gitProcesses = Get-Process -Name git -ErrorAction SilentlyContinue

    if ($gitProcesses) {
        foreach ($proc in $gitProcesses) {
            $runtime = [datetime]::Now - $proc.StartTime
            $shouldKill = $false

            # 若 ForceAll 或 運行超過 2 分鐘（正常 Git status 不應超過數十秒）
            if ($ForceAll -or ($runtime.TotalMinutes -ge 2)) {
                $shouldKill = $true
            }

            if ($shouldKill) {
                $targetId = $proc.Id
                $cpuTime = $proc.CPU
                $runtimeStr = "{0:N1} 分鐘" -f $runtime.TotalMinutes

                try {
                    # 使用 .NET 原生 Process 物件執行強制 Terminate
                    $procObj = [System.Diagnostics.Process]::GetProcessById($targetId)
                    $procObj.Kill()
                    $hasExited = $procObj.WaitForExit(3000)

                    # 再次確認進程是否真正脫離系統
                    Start-Sleep -Milliseconds 300
                    $checkAgain = Get-Process -Id $targetId -ErrorAction SilentlyContinue

                    if (-not $checkAgain) {
                        $killedCount++
                        Add-Content -Path $logPath -Value "[$now] [成功] 徹底終止卡死進程: PID $targetId (已運行 $runtimeStr, 消耗 CPU: $cpuTime 秒)"
                    } else {
                        $failCount++
                        Add-Content -Path $logPath -Value "[$now] [警告] 進程 PID $targetId 呼叫 Kill 後依然殘留 (Session 鎖定中)"
                    }
                } catch {
                    $failCount++
                    Add-Content -Path $logPath -Value "[$now] [失敗] 終止進程 PID $targetId 拋出例外: $_"
                }
            }
        }
    } else {
        Add-Content -Path $logPath -Value "[$now] 目前無任何 Git 進程運行，系統狀態正常。"
    }

    # 檢查並清除 d:\GOOGLE ANGET 主要倉庫的殘留 index.lock
    $lockFiles = @(
        "d:\GOOGLE ANGET\.git\index.lock",
        "d:\GOOGLE ANGET\my-ai-brain\.git\index.lock"
    )
    foreach ($lock in $lockFiles) {
        if (Test-Path $lock) {
            Remove-Item -Path $lock -Force -ErrorAction SilentlyContinue
            Add-Content -Path $logPath -Value "[$now] [修復] 已清除殘留鎖定檔: $lock"
        }
    }

    Add-Content -Path $logPath -Value "[$now] === 掃描完畢: 成功清理 $killedCount 個, 失敗 $failCount 個 ===`r`n"
} catch {
    Add-Content -Path $logPath -Value "[$now] 發生未預期錯誤: $_`r`n"
}
