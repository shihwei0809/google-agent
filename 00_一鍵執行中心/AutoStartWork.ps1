# 自動開工 Git 同步與多電腦備份自動合併腳本 (多電腦完全整合版)
Set-Location -Path "C:\GOOGLE ANGET"

Write-Host "[Auto-StartWork] 正在拉取主分支最新狀態..." -ForegroundColor Yellow
git pull origin main

# 抓取所有電腦的 remote auto-backup/* 分支
git fetch origin "+refs/heads/auto-backup/*:refs/remotes/origin/auto-backup/*"

$backupBranches = git branch -r --list "origin/auto-backup/*"

if ($backupBranches) {
    Write-Host "[Auto-StartWork] 偵測到收工備份分支，正在自動合併所有電腦的進度..." -ForegroundColor Cyan
    
    $mergedInfo = @()
    foreach ($b in $backupBranches) {
        $cleanBranch = $b.Trim()
        $branchComputer = $cleanBranch -replace "origin/auto-backup/", ""
        git merge $cleanBranch --no-edit -m "開工自動合併 [$branchComputer] 收工備份"
        $mergedInfo += $branchComputer
    }
    
    $compList = $mergedInfo -join ", "
    $lastCommitMsg = git log -1 --format="%s (%cd)" --date=format:"%Y-%m-%d %H:%M"
    
    $detailMsg = "【開工同步完成】`n`n已成功整合以下電腦的收工進度：`n[$compList]`n`n最新進度：$lastCommitMsg`n`n可以繼續開發囉！"
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($detailMsg, "開工同步成功", "OK", "Information")
} else {
    Write-Host "[Auto-StartWork] 遠端無備份分支，已維持最新 main 分支狀態。" -ForegroundColor Green
}
