# 自動開工 Git 同步與合併腳本 (方案一)
Set-Location -Path "C:\GOOGLE ANGET"

Write-Host "[Auto-StartWork] 正在拉取主分支最新狀態..." -ForegroundColor Yellow
git pull origin main

# 檢查遠端是否有 auto-backup 分支
$hasBackup = git ls-remote --heads origin auto-backup

if ($hasBackup) {
    Write-Host "[Auto-StartWork] 偵測到上次收工的 auto-backup 備份分支，正在自動合併..." -ForegroundColor Cyan
    git fetch origin auto-backup
    git merge origin/auto-backup --no-edit -m "開工自動合併收工備份"
    
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("【開工同步完成】`n已成功拉取並合併上次收工的 [auto-backup] 程式碼！`n可以繼續開發囉。", "開工同步成功", "OK", "Information")
} else {
    Write-Host "[Auto-StartWork] 遠端無 auto-backup 備份分支，已維持最新 main 分支狀態。" -ForegroundColor Green
}
