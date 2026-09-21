$ErrorActionPreference = "Stop"
$dateStr = Get-Date -Format "yyyyMMdd"
$sourceDir = "D:\GOOGLE ANGET"
$baseBackupDir = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份\00_最近7天收工快照"
$historyBackupDir = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份\01_歷史按月封存"
$targetBackupDir = Join-Path $baseBackupDir "${dateStr}_收工備份"

Write-Host "Creating backup directory: $targetBackupDir"
if (!(Test-Path $targetBackupDir)) {
    New-Item -ItemType Directory -Force -Path $targetBackupDir | Out-Null
}

Write-Host "Copying modified folders to backup..."
$foldersToCopy = @(
    "三合一單網頁架機伺服器",
    "三合一單自動產生器",
    "勝一三合一單產生系統",
    "勝一三合一單網頁架機伺服器"
)

foreach ($folder in $foldersToCopy) {
    $srcPath = Join-Path $sourceDir $folder
    $destPath = Join-Path $targetBackupDir $folder
    if (Test-Path $srcPath) {
        Write-Host "Backing up: $folder"
        Copy-Item -Path $srcPath -Destination $targetBackupDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Checking for backups older than 7 days..."
$cutoffDate = (Get-Date).AddDays(-7)
Get-ChildItem -Path $baseBackupDir -Directory | Where-Object { $_.CreationTime -lt $cutoffDate } | ForEach-Object {
    $monthFolder = Join-Path $historyBackupDir $_.CreationTime.ToString("yyyy年MM月")
    if (!(Test-Path $monthFolder)) {
        New-Item -ItemType Directory -Force -Path $monthFolder | Out-Null
    }
    Write-Host "Archiving old backup: $($_.Name) to $monthFolder"
    Move-Item -Path $_.FullName -Destination $monthFolder -Force
}

Write-Host "Backup completed successfully."
