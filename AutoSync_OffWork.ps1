# 自動收工 Git 自動 Commit & Push 同步腳本
Set-Location -Path "C:\GOOGLE ANGET"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$gitStatus = git status --porcelain

if ($gitStatus) {
    Write-Host "[Auto-Sync] 偵測到程式碼變更，開始 Commit 並且 Push 到 GitHub..." -ForegroundColor Yellow
    git add -A
    git commit -m "[Auto-Sync] 自動收工同步 ($timestamp)"
    git push origin main
    
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("【自動收工完成】`n已將今日修改自動 Commit 並 Push 至 GitHub！`n時間: $timestamp", "自動收工同步", "OK", "Information")
} else {
    Write-Host "[Auto-Sync] 目前無變更需同步。" -ForegroundColor Green
}
