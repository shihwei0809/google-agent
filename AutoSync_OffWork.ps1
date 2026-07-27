# 自動收工 Git 自動 Commit & Push 至 auto-backup 分支腳本 (方案 B)
Set-Location -Path "C:\GOOGLE ANGET"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$gitStatus = git status --porcelain

if ($gitStatus) {
    Write-Host "[Auto-Backup] 偵測到程式碼變更，開始 Commit 並推送到 auto-backup 備份分支..." -ForegroundColor Yellow
    git add -A
    git commit -m "[Auto-Backup] 自動收工備份 ($timestamp)"
    
    # 推送到 GitHub 的 auto-backup 備份分支，不污染 main 分支
    git push origin HEAD:refs/heads/auto-backup --force
    
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("【自動收工完成】`n已將今日修改自動 Commit 並安全備份推送到 GitHub 的 [auto-backup] 分支！`n時間: $timestamp", "自動收工同步 (方案 B)", "OK", "Information")
} else {
    Write-Host "[Auto-Backup] 目前無變更需同步。" -ForegroundColor Green
}
