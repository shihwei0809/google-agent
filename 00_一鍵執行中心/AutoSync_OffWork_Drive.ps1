# AutoSync_OffWork_Drive.ps1
# 自動將當天有修改的專案資料夾與檔案同步備份至 Google Drive 00_最近7天收工快照
# 遵循中央大腦 Rule 11 (動態偵測 Google Drive 掛載磁碟) 與 Rule 12 (Git 與備份效能防護)
# 並自動執行滾動封存：檢查 00_最近7天收工快照，將超過 7 天之備份資料夾移動至 01_歷史按月封存\YYYY年MM月

$srcRoot = if (Test-Path "C:\GOOGLE ANGET") { "C:\GOOGLE ANGET" } elseif (Test-Path "D:\GOOGLE ANGET") { "D:\GOOGLE ANGET" } else { "C:\GOOGLE ANGET" }
$todayStr = (Get-Date).ToString("yyyyMMdd")

# Rule 11: 動態偵測 Google Drive 掛載磁碟 (絕對不寫死磁碟機代號)
$gdriveRoot = $null
foreach ($drive in [System.IO.DriveInfo]::GetDrives()) {
    if ($drive.IsReady) {
        $candidate1 = Join-Path $drive.RootDirectory.FullName "我的雲端硬碟"
        $candidate2 = Join-Path $drive.RootDirectory.FullName "My Drive"
        if (Test-Path -LiteralPath $candidate1) {
            $gdriveRoot = $candidate1
            break
        } elseif (Test-Path -LiteralPath $candidate2) {
            $gdriveRoot = $candidate2
            break
        }
    }
}

if (-not $gdriveRoot) {
    Write-Host "[!] 錯誤：未找到 Google Drive 掛載磁碟 (找不到 '我的雲端硬碟' 或 'My Drive')" -ForegroundColor Red
    exit 1
}

Write-Host "[Google Drive] 偵測到雲端硬碟根目錄: $gdriveRoot" -ForegroundColor Green

$backupBase = Join-Path $gdriveRoot "GOOGLE ANGET\專案備份"
$snapshotRoot = Join-Path $backupBase "00_最近7天收工快照"
$archiveRoot = Join-Path $backupBase "01_歷史按月封存"
$destRoot = Join-Path $snapshotRoot ($todayStr + "_收工備份")

if (!(Test-Path -LiteralPath $destRoot)) {
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[AutoSync] 掃描今日 (00:00 起) 修改過之專案與檔案..." -ForegroundColor Yellow
Write-Host "Source: $srcRoot" -ForegroundColor Gray
Write-Host "Destination: $destRoot" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan

# 1. 取得今日 (00:00起) 修改過的檔案 (嚴格排除依賴、快取與大型歷史封存庫)
$cutoff = (Get-Date).Date
$ignoreRegex = "node_modules|venv|\\.git|\\.netlify|\\.wrangler|\\.firebase|\\.vscode|\\old(\\|$)|category_folders_backup|skills_backup|教育訓練教材|cross-device-agent-skills|my-ai-brain|專案備份"

$modifiedFiles = Get-ChildItem -Path $srcRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.LastWriteTime -ge $cutoff -and
        $_.FullName -notmatch $ignoreRegex
    }

$copiedTargets = @{}
$ignoredTopFolders = @(".git", "node_modules", "venv", ".venv", ".netlify", ".wrangler", ".firebase", ".vscode", "old", "category_folders_backup", "skills_backup", "教育訓練教材", "cross-device-agent-skills", "my-ai-brain", "專案備份")

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
        Write-Host "[Backup] 複製根目錄檔案: $($parts[0])" -ForegroundColor Green
    } else {
        # 判斷是否為分類大資料夾 (第一類、第二類、第三類、第四類)
        $subProjRel = if ($parts[0] -match "^第[一二三四五]類" -and $parts.Length -ge 2) {
            Join-Path $parts[0] $parts[1]
        } else {
            $parts[0]
        }
        if ($ignoredTopFolders -contains $parts[0]) { continue }
        if (-not $copiedTargets.ContainsKey($subProjRel)) {
            $srcFolder = Join-Path $srcRoot $subProjRel
            $destFolder = Join-Path $destRoot $subProjRel
            if (Test-Path -Path $srcFolder -PathType Container) {
                Write-Host "[Backup] 同步修改之子專案: $subProjRel" -ForegroundColor Cyan
                robocopy $srcFolder $destFolder /E /R:1 /W:1 /XD .git node_modules venv .venv .netlify .wrangler .firebase .vscode __pycache__ /XF *.sqlite *.sqlite-wal *.sqlite-shm *.zip *.avi *.mp4 *.wav *.mp3 *.bin *.pt *.pth *.onnx *.safetensors /NDL /NFL /NJH /NJS | Out-Null
                $copiedTargets[$subProjRel] = $true
            }
        }
    }
}

Write-Host "==========================================" -ForegroundColor Green
Write-Host "[AutoSync] 今日備份順利完成！目的地: $destRoot" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 4. 【滾動封存防爆機制】檢查 00_最近7天收工快照，超過 7 天者自動移至 01_歷史按月封存
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[Rolling Archive] 檢查 00_最近7天收工快照，自動滾動封存超過 7 天之舊備份..." -ForegroundColor Yellow
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
                Write-Host "[Archived] 已自動移轉舊快照: $folderName -> 01_歷史按月封存\$monthStr" -ForegroundColor Yellow
            } else {
                Write-Host "[Keep] 保留 7 天內快照: $folderName" -ForegroundColor Gray
            }
        } catch {
            Write-Host "[Warning] 無法解析資料夾日期: $folderName" -ForegroundColor Red
        }
    }
}
Write-Host "[Rolling Archive] 00_最近7天收工快照維持乾淨窗口。" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

