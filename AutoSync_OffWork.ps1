# 自動收工 Git 自動 Commit & Push 至 電腦專屬備份分支 (方案 B 多電腦不覆蓋防護版) + G槽異動備份
Set-Location -Path "C:\GOOGLE ANGET"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$today = Get-Date -Format "yyyyMMdd"
$computerName = $env:COMPUTERNAME
$backupBranch = "auto-backup/$computerName"
$gitStatus = git status --porcelain

Write-Host "=================================================="
Write-Host "🚀 啟動自動收工程序 ($timestamp)"
Write-Host "=================================================="

# ==========================================
# 1. Git 備份處理
# ==========================================
if ($gitStatus) {
    Write-Host "[Auto-Backup] 偵測到程式碼變更，開始 Commit 並推送到 [$backupBranch] 備份分支..." -ForegroundColor Yellow
    git add -A
    git commit -m "[Auto-Backup] [$computerName] 自動收工備份 ($timestamp)"
    git push origin "HEAD:refs/heads/$backupBranch" --force
    Write-Host "✅ Git 分支同步完成！" -ForegroundColor Green
} else {
    Write-Host "[Auto-Backup] 目前無 Git 變更需同步。" -ForegroundColor Green
}

# ==========================================
# 2. G槽 雲端硬碟異動備份處理 (依照新規範)
# ==========================================
Write-Host "`n[Auto-Backup] 準備執行 Google Drive 異動備份..." -ForegroundColor Yellow

# 動態尋找「我的雲端硬碟」掛載點 (掃描常見槽位)
$driveFound = $false
$backupRoot = ""
$drives = @("G:\", "D:\", "E:\", "F:\", "C:\Users\$env:USERNAME\Google Drive\", "C:\")

foreach ($drive in $drives) {
    $testPath = Join-Path $drive "我的雲端硬碟\GOOGLE ANGET\專案備份"
    if (Test-Path $testPath) {
        $backupRoot = $testPath
        $driveFound = $true
        break
    }
}

if (-not $driveFound) {
    Write-Host "⚠️ 找不到『我的雲端硬碟\GOOGLE ANGET\專案備份』資料夾，跳過 G 槽備份。" -ForegroundColor Red
} else {
    $recentBackupDir = Join-Path $backupRoot "00_最近7天收工快照"
    $archiveDirRoot = Join-Path $backupRoot "01_歷史按月封存"

    if (!(Test-Path $recentBackupDir)) { New-Item -ItemType Directory -Path $recentBackupDir -Force | Out-Null }
    if (!(Test-Path $archiveDirRoot)) { New-Item -ItemType Directory -Path $archiveDirRoot -Force | Out-Null }

    $targetDirName = "${today}_收工備份"
    $targetPath = Join-Path $recentBackupDir $targetDirName

    Write-Host "開始進行【異動資料】備份至: $targetPath"

    $robocopyArgs = @(
        "C:\GOOGLE ANGET",
        $targetPath,
        "/S", 
        "/MAXAGE:$today",
        "/XD", ".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", "venv",
        "/XF", "*.pyc",
        "/R:0", "/W:0",
        "/NFL", "/NDL", "/NJH", "/NJS", "/nc", "/ns", "/np"
    )
    & robocopy $robocopyArgs | Out-Null
    Write-Host "✅ 雲端硬碟異動備份完成: $targetDirName" -ForegroundColor Green

    # 滾動封存
    $cutoffDate = (Get-Date).AddDays(-7)
    $dirs = Get-ChildItem -Path $recentBackupDir -Directory

    foreach ($dir in $dirs) {
        if ($dir.Name -match "^(\d{8})(_\d+)?_收工備份$") {
            $dateStr = $matches[1]
            try {
                $dirDate = [datetime]::ParseExact($dateStr, "yyyyMMdd", $null)
                if ($dirDate -lt $cutoffDate) {
                    $archiveMonth = $dirDate.ToString("yyyy年MM月")
                    $archiveTarget = Join-Path $archiveDirRoot $archiveMonth
                    if (!(Test-Path $archiveTarget)) {
                        New-Item -ItemType Directory -Path $archiveTarget -Force | Out-Null
                    }
                    $moveTarget = Join-Path $archiveTarget $dir.Name
                    Move-Item -Path $dir.FullName -Destination $moveTarget -Force
                    Write-Host "📦 已封存歷史備份: $($dir.Name) -> $archiveMonth" -ForegroundColor Cyan
                }
            } catch {}
        }
    }
}

Write-Host "=================================================="
Write-Host "🎉 每日自動收工程序全部完成！"
Write-Host "=================================================="
