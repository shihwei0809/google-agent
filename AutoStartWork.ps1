# 自動開工 Git 同步與進度提醒腳本 (方案一增強版)
Set-Location -Path "C:\GOOGLE ANGET"

Write-Host "[Auto-StartWork] 正在拉取主分支最新狀態..." -ForegroundColor Yellow
git pull origin main

# 檢查遠端是否有 auto-backup 分支
$hasBackup = git ls-remote --heads origin auto-backup

if ($hasBackup) {
    Write-Host "[Auto-StartWork] 偵測到上次收工備份，分析前次修改進度..." -ForegroundColor Cyan
    git fetch origin auto-backup
    
    # 取得前次修改檔案與 Commit 訊息
    $lastCommitMsg = git log -1 --format="%s (%cd)" --date=format:"%Y-%m-%d %H:%M" origin/auto-backup
    $changedFiles = git diff --name-only main...origin/auto-backup
    
    # 合併收工備份
    git merge origin/auto-backup --no-edit -m "開工自動合併收工備份"
    
    $fileListStr = if ($changedFiles) { ($changedFiles -join "`n") } else { "（無檔案異動列表）" }
    $detailMsg = "【開工進度提醒】`n`n🕒 上次收工紀錄：$lastCommitMsg`n`n📁 上次修改的檔案：`n$fileListStr`n`n程式碼已自動合併，可以繼續開發囉！"
    
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($detailMsg, "開工進度提醒", "OK", "Information")
} else {
    Write-Host "[Auto-StartWork] 遠端無 auto-backup 備份分支，已維持最新 main 分支狀態。" -ForegroundColor Green
}
