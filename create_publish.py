import os

ps_script = """# 一鍵將備份分支合併並發布至 main 主線腳本
Set-Location -Path "C:\\GOOGLE ANGET"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$computerName = $env:COMPUTERNAME
$backupBranch = "origin/auto-backup/$computerName"

Write-Host "[PublishToMain] 正在準備將當前備份進度發布至 main 主線..." -ForegroundColor Yellow

# 1. 確保 main 是最新狀態
git checkout main
git pull origin main

# 2. 抓取備份分支並進行合併發布
git fetch origin "+refs/heads/auto-backup/*:refs/remotes/origin/auto-backup/*"
$hasBackup = git branch -r --list $backupBranch

if ($hasBackup) {
    git merge $backupBranch --no-edit -m "release: 專案/功能完成，正式合併發布至 main 主線 ($timestamp)"
    git push origin main
    
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("【正式發布成功】`n已將 [$computerName] 的進度正式合併並 Push 至 GitHub main 主線！", "發布至主線", "OK", "Information")
} else {
    git add -A
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        git commit -m "release: 正式完成並發布至 main 主線 ($timestamp)"
        git push origin main
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show("【正式發布成功】`n已將當前專案程式碼正式 Commit 並 Push 至 main 主線！", "發布至主線", "OK", "Information")
    } else {
        Write-Host "[PublishToMain] 目前 main 主線已是最新狀態，無需重複發布。" -ForegroundColor Green
    }
}
"""

with open(r"C:\GOOGLE ANGET\PublishToMain.ps1", "w", encoding="utf-8-sig") as f:
    f.write(ps_script)

print("Created C:\\GOOGLE ANGET\\PublishToMain.ps1 successfully!")
