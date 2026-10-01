$today = Get-Date -Format "yyyyMMdd"
$drivePath = $null
foreach ($drive in (Get-PSDrive -PSProvider FileSystem).Root) {
    $testPath = Join-Path $drive "我的雲端硬碟\GOOGLE ANGET\專案備份"
    if (Test-Path $testPath) {
        $drivePath = $testPath
        break
    }
}

if ($null -eq $drivePath) {
    Write-Host "找不到 Google Drive 的專案備份資料夾，請確認 Google Drive 是否已經掛載！"
    exit 1
}

Write-Host "偵測到 Google Drive 備份目錄: $drivePath"
$recentBackupDir = Join-Path $drivePath "00_最近7天收工快照"
$archiveDir = Join-Path $drivePath "01_歷史按月封存"

if (-not (Test-Path $recentBackupDir)) { New-Item -ItemType Directory -Path $recentBackupDir | Out-Null }
if (-not (Test-Path $archiveDir)) { New-Item -ItemType Directory -Path $archiveDir | Out-Null }

# Rolling Archive
$folders = Get-ChildItem -Path $recentBackupDir -Directory
foreach ($f in $folders) {
    if ($f.Name -match "^(\d{4})(\d{2})\d{2}_收工備份$") {
        $year = $matches[1]
        $month = $matches[2]
        $dateStr = $matches[0].Substring(0, 8)
        $folderDate = [datetime]::ParseExact($dateStr, "yyyyMMdd", $null)
        if ((Get-Date) - $folderDate -gt [timespan]::FromDays(7)) {
            $monthArchive = Join-Path $archiveDir "${year}年${month}月"
            if (-not (Test-Path $monthArchive)) { New-Item -ItemType Directory -Path $monthArchive | Out-Null }
            Write-Host "封存舊備份: $($f.Name) -> $monthArchive"
            Move-Item -Path $f.FullName -Destination $monthArchive
        }
    }
}

# Robocopy today's files
$todayBackupPath = Join-Path $recentBackupDir "${today}_收工備份"
if (-not (Test-Path $todayBackupPath)) { New-Item -ItemType Directory -Path $todayBackupPath | Out-Null }

Write-Host "========================================="
Write-Host "開始執行 Robocopy 異動備份 (僅備份今天有異動的檔案)..."
Write-Host "目標路徑: $todayBackupPath"
robocopy "C:\GOOGLE ANGET" $todayBackupPath /S /MAXAGE:$today /XD .git node_modules __pycache__ .wrangler /NJH /NJS /NDL /NC /NS /NP
$rc = $LASTEXITCODE
Write-Host "Robocopy 結束代碼: $rc"
if ($rc -ge 8) {
    Write-Host "備份發生錯誤！"
} else {
    Write-Host "備份成功完成！"
}
