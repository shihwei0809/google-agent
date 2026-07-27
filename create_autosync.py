import os

ps_script = """# 自動收工 Git 自動 Commit & Push 至 電腦專屬備份分支 (方案 B 多電腦不覆蓋防護版)
Set-Location -Path "C:\\GOOGLE ANGET"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$computerName = $env:COMPUTERNAME
$backupBranch = "auto-backup/$computerName"
$gitStatus = git status --porcelain

if ($gitStatus) {
    Write-Host "[Auto-Backup] 偵測到程式碼變更，開始 Commit 並推送到 [$backupBranch] 備份分支..." -ForegroundColor Yellow
    git add -A
    git commit -m "[Auto-Backup] [$computerName] 自動收工備份 ($timestamp)"
    
    # 推送到該電腦專屬的 auto-backup/電腦名稱 分支，絕對不會覆蓋另一台電腦的備份！
    git push origin "HEAD:refs/heads/$backupBranch" --force
    
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("【自動收工完成】`n已將本台電腦 [$computerName] 的修改安全備份至 GitHub 的 [$backupBranch] 分支！`n時間: $timestamp", "自動收工同步", "OK", "Information")
} else {
    Write-Host "[Auto-Backup] 目前無變更需同步。" -ForegroundColor Green
}
"""

with open(r"C:\GOOGLE ANGET\AutoSync_OffWork.ps1", "w", encoding="utf-8-sig") as f:
    f.write(ps_script)

print("Updated C:\\GOOGLE ANGET\\AutoSync_OffWork.ps1 for multi-computer isolation successfully!")
