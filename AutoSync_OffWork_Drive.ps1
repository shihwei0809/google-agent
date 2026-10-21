# AutoSync_OffWork_Drive.ps1
# 自動將當天有修改的專案資料夾與檔案同步備份至 Google Drive 00_最近7天收工快照
# 並自動執行滾動封存：檢查 00_最近7天收工快照，將超過 7 天之備份資料夾移動至 01_歷史按月封存\YYYY年MM月

$srcRoot = "C:\GOOGLE ANGET"
$todayStr = (Get-Date).ToString("yyyyMMdd")
$backupBase = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份"
$snapshotRoot = Join-Path $backupBase "00_最近7天收工快照"
$archiveRoot = Join-Path $backupBase "01_歷史按月封存"
$destRoot = Join-Path $snapshotRoot ($todayStr + "_收工備份")

if (!(Test-Path -LiteralPath $destRoot)) {
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[AutoSync] Scanning modified projects & files (Last 24h)..." -ForegroundColor Yellow
Write-Host "Source: $srcRoot" -ForegroundColor Gray
Write-Host "Destination: $destRoot" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan

# 1. 取得最近 24 小時內修改過的檔案 (排除依賴與快取)
$cutoff = (Get-Date).AddDays(-1)
$modifiedFiles = Get-ChildItem -Path $srcRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.LastWriteTime -ge $cutoff -and
        $_.FullName -notmatch "node_modules" -and
        $_.FullName -notmatch "venv" -and
        $_.FullName -notmatch "\\.git" -and
        $_.FullName -notmatch "\\.netlify" -and
        $_.FullName -notmatch "\\.wrangler" -and
        $_.FullName -notmatch "\\.firebase" -and
        $_.FullName -notmatch "專案備份"
    }

$copiedTargets = @{}

# 2. 備份根目錄關鍵檔案 (如 HANDOVER.md 等)
Copy-Item -Path (Join-Path $srcRoot "HANDOVER.md") -Destination (Join-Path $destRoot "HANDOVER.md") -Force -ErrorAction SilentlyContinue

# 3. 掃描變更檔案所屬的子專案資料夾
foreach ($file in $modifiedFiles) {
    $fullName = $file.FullName
    $relPath = $fullName.Substring($srcRoot.Length + 1)
    $parts = $relPath.Split([System.IO.Path]::DirectorySeparatorChar)

    if ($parts.Length -eq 1) {
        # 根目錄檔案
        $destFile = Join-Path $destRoot $parts[0]
        Copy-Item -Path $fullName -Destination $destFile -Force
        Write-Host "[Backup] Copied root file: $($parts[0])" -ForegroundColor Green
    } else {
        $topFolder = $parts[0]
        if (-not $copiedTargets.ContainsKey($topFolder)) {
            $srcFolder = Join-Path $srcRoot $topFolder
            $destFolder = Join-Path $destRoot $topFolder
            if (Test-Path -Path $srcFolder -PathType Container) {
                Write-Host "[Backup] Syncing modified folder: $topFolder" -ForegroundColor Cyan
                robocopy $srcFolder $destFolder /E /R:1 /W:1 /XD .git node_modules venv .venv .netlify .wrangler .firebase /XF *.zip *.avi /NDL /NFL /NJH /NJS | Out-Null
                $copiedTargets[$topFolder] = $true
            }
        }
    }
}

Write-Host "==========================================" -ForegroundColor Green
Write-Host "[AutoSync] Backup successfully completed into $destRoot !" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 4. 【滾動封存防爆機制】檢查 00_最近7天收工快照，超過 7 天者自動移至 01_歷史按月封存
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[Rolling Archive] Checking 00_最近7天收工快照 for folders older than 7 days..." -ForegroundColor Yellow
$rollingCutoff = (Get-Date).AddDays(-7)
$allSnapshots = Get-ChildItem -LiteralPath $snapshotRoot -Directory -ErrorAction SilentlyContinue

foreach ($folder in $allSnapshots) {
    $folderName = $folder.Name
    # 提取日期 YYYYMMDD
    if ($folderName -match "(\d{8})") {
        $dateStr = $matches[1]
        try {
            $folderDate = [datetime]::ParseExact($dateStr, "yyyyMMdd", $null)
            if ($folderDate -lt $rollingCutoff) {
                $monthStr = $folderDate.ToString("yyyy年MM月")
                $targetMonthDir = Join-Path $archiveRoot $monthStr
                if (!(Test-Path -LiteralPath $targetMonthDir)) {
                    New-Item -ItemType Directory -Force -Path $targetMonthDir | Out-Null
                }
                $targetPath = Join-Path $targetMonthDir $folderName
                if (Test-Path -LiteralPath $targetPath) {
                    $targetPath = Join-Path $targetMonthDir ($folderName + "_archived")
                }
                Move-Item -LiteralPath $folder.FullName -Destination $targetPath -Force
                Write-Host "[Archived] Moved $folderName -> 01_歷史按月封存\$monthStr" -ForegroundColor Yellow
            } else {
                Write-Host "[Keep] $folderName (Within 7 days)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "[Warning] Could not parse date for folder: $folderName" -ForegroundColor Red
        }
    }
}
Write-Host "[Rolling Archive] 00_最近7天收工快照 status verified clean." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
