# AutoSync_OffWork_Drive.ps1
# 自動將當天有修改的專案資料夾與檔案同步備份至 Google Drive 00_最近7天收工快照

$srcRoot = "C:\GOOGLE ANGET"
$todayStr = (Get-Date).ToString("yyyyMMdd")
$snapshotRoot = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份\00_最近7天收工快照"
$destRoot = Join-Path $snapshotRoot ($todayStr + "_收工備份")

if (!(Test-Path -Path $destRoot)) {
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

# 2. 備份根目錄檔案 (如 HANDOVER.md 等)
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