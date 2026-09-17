# Auto_Snapshot_Backup.ps1
# 自動掃描 24 小時內修改過的專案並執行 7 天滾動收工快照備份

$srcRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($srcRoot)) {
    $srcRoot = Get-Location
}
$dateStr = Get-Date -Format "yyyyMMdd"
$destBase = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份\00_最近7天收工快照\${dateStr}_收工備份"

Write-Host "🔍 [收工快照] 正在深層掃描 24 小時內有異動的檔案..." -ForegroundColor Yellow

# 1. 抓取最近 24 小時內修改過的檔案 (排除常見的暫存與模組資料夾)
$modifiedFiles = Get-ChildItem -Path $srcRoot -Recurse -File -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.LastWriteTime -ge (Get-Date).AddDays(-1) -and 
        $_.FullName -notmatch "\\node_modules\\" -and 
        $_.FullName -notmatch "\\venv\\" -and 
        $_.FullName -notmatch "\\\.venv\\" -and 
        $_.FullName -notmatch "\\\.git\\" -and
        $_.FullName -notmatch "\\\.netlify\\" -and
        $_.FullName -notmatch "\\\.wrangler\\" -and
        $_.FullName -notmatch "\\\.firebase\\" -and
        $_.FullName -notmatch "\\__pycache__\\"
    }

if (!$modifiedFiles) {
    Write-Host "✅ [收工快照] 今日無任何檔案修改，無須備份。" -ForegroundColor Green
    exit 0
}

# 2. 判斷這些檔案屬於哪些「子專案資料夾」
$projectsToBackup = @()
$categories = @("第一類_核心網頁與互動系統", "第二類_生產管理與API串接", "第三類_AI代理與指南企劃", "說明書", "檔案類_核心網頁與互動系統")

foreach ($file in $modifiedFiles) {
    # 取得相對路徑
    $relPath = $file.FullName.Substring($srcRoot.Length + 1)
    $parts = $relPath.Split([System.IO.Path]::DirectorySeparatorChar)
    
    if ($parts.Length -eq 1) {
        # 根目錄下的獨立檔案，直接記錄檔案路徑
        $projPath = $file.FullName
    } else {
        $category = $parts[0]
        if ($category -in $categories) {
            # 在分類目錄下的子專案 (例如 第一類/某個系統/)
            if ($parts.Length -gt 1) {
                $projPath = Join-Path $srcRoot (Join-Path $category $parts[1])
            } else {
                $projPath = $file.FullName
            }
        } else {
            # 第一層的專案資料夾 (例如 三合一單自動產生器/)
            $projPath = Join-Path $srcRoot $category
        }
    }
    
    if ($projectsToBackup -notcontains $projPath) {
        $projectsToBackup += $projPath
    }
}

# 確保目的地存在
if (!(Test-Path $destBase)) {
    New-Item -ItemType Directory -Force -Path $destBase | Out-Null
}

# 3. 開始備份
Write-Host "🚀 [收工快照] 找到以下有異動的專案/檔案，開始備份：" -ForegroundColor Cyan
foreach ($proj in $projectsToBackup) {
    $itemName = Split-Path $proj -Leaf
    $destPath = Join-Path $destBase $itemName
    
    if (Test-Path $proj -PathType Container) {
        Write-Host "   -> 備份資料夾：$itemName"
        robocopy $proj $destPath /E /R:1 /W:1 /XD .git node_modules venv .venv .netlify .wrangler .firebase __pycache__ /XF *.zip /NDL /NFL /NJH /NJS | Out-Null
    } else {
        Write-Host "   -> 備份檔案：$itemName"
        Copy-Item -Path $proj -Destination $destBase -Force
    }
}

# 4. 滾動封存機制 (大於 7 天移至歷史封存)
Write-Host "🔄 [收工快照] 執行 7 天歷史滾動封存檢查..." -ForegroundColor Yellow
$snapshotDir = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份\00_最近7天收工快照"
$archiveBase = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份\01_歷史按月封存"

if (Test-Path $snapshotDir) {
    $folders = Get-ChildItem -Path $snapshotDir -Directory
    $thresholdDate = (Get-Date).AddDays(-7)

    foreach ($folder in $folders) {
        if ($folder.CreationTime -lt $thresholdDate) {
            $monthStr = $folder.CreationTime.ToString("yyyy年MM月")
            $archivePath = Join-Path $archiveBase $monthStr
            if (!(Test-Path $archivePath)) {
                New-Item -ItemType Directory -Force -Path $archivePath | Out-Null
            }
            Move-Item -Path $folder.FullName -Destination $archivePath -Force
            Write-Host "📦 已將超過 7 天的歷史備份 $($folder.Name) 封存至 $archivePath" -ForegroundColor Magenta
        }
    }
}

Write-Host "🎉 [收工快照] 本機備份與封存處理全部完成！" -ForegroundColor Green
