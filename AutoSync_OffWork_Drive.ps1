# ==========================================
# AutoSync_OffWork_Drive.ps1
# 依據 Rule 4 & Rule 11：
# 1. 動態偵測 Google Drive（掃描含有「我的雲端硬碟」或「My Drive」之磁碟）
# 2. 自動滾動封存超過 7 天的快照至 01_歷史按月封存\YYYY年MM月
# 3. 僅同步今日 (00:00 起) 修改之子專案至 00_最近7天收工快照\yyyyMMdd_收工備份
# ==========================================

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Output "============================================================"
Write-Output "啟動收工雙重備份程序 (AutoSync_OffWork_Drive.ps1)"
Write-Output "============================================================"

# 1. 動態偵測 Google Drive 掛載磁碟
$driveRoot = $null
$drives = Get-PSDrive -PSProvider FileSystem
foreach ($d in $drives) {
    $p1 = Join-Path $d.Root "我的雲端硬碟"
    $p2 = Join-Path $d.Root "My Drive"
    if (Test-Path $p1) {
        $driveRoot = $p1
        break
    } elseif (Test-Path $p2) {
        $driveRoot = $p2
        break
    }
}

if (-not $driveRoot) {
    Write-Output "[ERROR] 找不到 Google Drive 掛載磁碟（未偵測到『我的雲端硬碟』或『My Drive』）！"
    exit 1
}

Write-Output "[OK] 動態偵測到 Google Drive 路徑: $driveRoot"

$backupBase = Join-Path $driveRoot "GOOGLE ANGET\專案備份"
$recentDir  = Join-Path $backupBase "00_最近7天收工快照"
$archiveDir = Join-Path $backupBase "01_歷史按月封存"

New-Item -ItemType Directory -Force -Path $recentDir | Out-Null
New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

$todayStr = (Get-Date).ToString("yyyyMMdd")
$todayStart = (Get-Date).Date
$cutoffDate = $todayStart.AddDays(-7)

# 2. 自動滾動封存超過 7 天的歷史快照
Write-Output "------------------------------------------------------------"
Write-Output "[STEP 1] 檢查 00_最近7天收工快照 滾動封存 (保留 7 天內: >= $($cutoffDate.ToString('yyyy-MM-dd')))"
$existingSnapshots = Get-ChildItem -Path $recentDir -Directory
$archivedCount = 0
foreach ($snap in $existingSnapshots) {
    if ($snap.Name -match "^(\d{4})(\d{2})(\d{2})") {
        $y = [int]$Matches[1]
        $m = [int]$Matches[2]
        $d = [int]$Matches[3]
        try {
            $snapDate = Get-Date -Year $y -Month $m -Day $d -Hour 0 -Minute 0 -Second 0
            if ($snapDate -lt $cutoffDate) {
                $ymStr = "{0:D4}年{1:D2}月" -f $y, $m
                $monthFolder = Join-Path $archiveDir $ymStr
                New-Item -ItemType Directory -Force -Path $monthFolder | Out-Null
                $destSnap = Join-Path $monthFolder $snap.Name
                Write-Output "  -> 歸檔超期快照: $($snap.Name) -> 01_歷史按月封存\$ymStr"
                Move-Item -Path $snap.FullName -Destination $destSnap -Force
                $archivedCount++
            }
        } catch {}
    }
}
if ($archivedCount -eq 0) {
    Write-Output "  -> 無超過 7 天之快照需歸檔，目錄保持乾淨。"
}

# 3. 同步今日修改之子專案與根目錄核心檔案
$targetSnapshot = Join-Path $recentDir ("{0}_收工備份" -f $todayStr)
New-Item -ItemType Directory -Force -Path $targetSnapshot | Out-Null
Write-Output "------------------------------------------------------------"
Write-Output "[STEP 2] 今日收工快照目標: $targetSnapshot"

$sourceRoot = "C:\GOOGLE ANGET"
$excludeDirs = @(".git", "node_modules", "__pycache__", ".wrangler", "build", "venv", ".venv", "old", "專案備份", "category_folders_backup", "skills_backup", "my-ai-brain", "cross-device-agent-skills")

# 複製根目錄今日修改之檔案 (如 HANDOVER.md, .gitignore 等)
$rootFiles = Get-ChildItem -Path $sourceRoot -File | Where-Object { $_.LastWriteTime -ge $todayStart }
foreach ($rf in $rootFiles) {
    Copy-Item -Path $rf.FullName -Destination (Join-Path $targetSnapshot $rf.Name) -Force
    Write-Output "  -> 已同步根目錄檔案: $($rf.Name)"
}

# 檢查各子資料夾今日是否有修改
$subDirs = Get-ChildItem -Path $sourceRoot -Directory | Where-Object { $excludeDirs -notcontains $_.Name }
$syncedProjects = @()

foreach ($dir in $subDirs) {
    $modifiedFiles = Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $_.LastWriteTime -ge $todayStart -and
        $_.FullName -notmatch "\\(\.git|node_modules|__pycache__|\.wrangler|build|venv|\.venv)\\"
    }
    if ($modifiedFiles -and $modifiedFiles.Count -gt 0) {
        $destProj = Join-Path $targetSnapshot $dir.Name
        Write-Output "  -> 同步今日異動子專案: $($dir.Name) (異動檔案數: $($modifiedFiles.Count))"
        # 依據差異化備份規範：程式碼與今日修改之檔案同步，排除暫存目錄與大型舊安裝包
        $rcArgs = @(
            $dir.FullName,
            $destProj,
            "/E",
            "/XO",
            "/MAXAGE:1",
            "/XD", ".wrangler", "node_modules", ".git", "__pycache__", "build", "venv", ".venv",
            "/XF", "*.sqlite", "*.sqlite-wal", "*.sqlite-shm", "security_config.json", "*.exe",
            "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS"
        )
        & robocopy @rcArgs | Out-Null
        $syncedProjects += $dir.Name
    }
}

# 額外同步今日修改之 C:\notype-master 原始碼 (不含 node_modules 與 dist 大型 exe)
if (Test-Path "C:\notype-master") {
    $notypeMod = Get-ChildItem -Path "C:\notype-master\src" -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $todayStart }
    if ($notypeMod -and $notypeMod.Count -gt 0) {
        $destNotype = Join-Path $targetSnapshot "notype-master"
        Write-Output "  -> 同步今日異動專案: C:\notype-master -> notype-master (異動檔案數: $($notypeMod.Count))"
        $rcArgs2 = @(
            "C:\notype-master",
            $destNotype,
            "/E",
            "/XO",
            "/XD", "node_modules", ".git", "dist", "build",
            "/XF",
            "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS"
        )
        & robocopy @rcArgs2 | Out-Null
        $syncedProjects += "notype-master"
    }
}

Write-Output "------------------------------------------------------------"



Write-Output "[DONE] 收工備份完成！共計同步 $($syncedProjects.Count) 個今日異動專案: $($syncedProjects -join ', ')"
Write-Output "============================================================"
