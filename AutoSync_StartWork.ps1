# C:\GOOGLE ANGET\AutoSync_StartWork.ps1
# 跨電腦開工【三軌合一智慧對齊】自動化執行腳本
# 涵蓋：1. Git 分支智慧合併 2. Google Drive 實體二進位檔案鏡像 3. 中央大腦同步

$ErrorActionPreference = "Continue"
$projectRoot = "C:\GOOGLE ANGET"
$driveBackupRoot = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份"
$aiBrainRoot = Join-Path $env:USERPROFILE ".ai"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 開始執行【三軌合一智慧開工同步】..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# -------------------------------------------------------------------------
# 軌道 1：Git 全分支自動掃描、暫存與無損拉取
# -------------------------------------------------------------------------
Write-Host "`n📡 [軌道 1/3] 執行 Git 代碼倉庫同步..." -ForegroundColor Yellow
Set-Location $projectRoot

# 1. 檢查並保護本地未存檔檔案
$hasChanges = (git status --porcelain)
$stashed = $false
if ($hasChanges) {
    Write-Host "📦 偵測到本地未存檔變更，自動執行安全暫存 (git stash)..." -ForegroundColor Magenta
    git stash | Out-Null
    $stashed = $true
}

# 2. 抓取遠端最新快照
Write-Host "🔄 正在獲取遠端所有分支快照 (git fetch --all)..."
git fetch --all --tags --prune | Out-Null

# 3. 智慧尋找最新 feat/YYYYMMDD 或 dev 分支
$remoteBranches = git branch -r | ForEach-Object { $_.Trim() }
$latestFeatBranch = $remoteBranches | Where-Object { $_ -match "origin/feat/\d{8}" } | Sort-Object -Descending | Select-Object -First 1

if ($latestFeatBranch) {
    $branchName = $latestFeatBranch -replace "^origin/", ""
    Write-Host "🎯 偵測到遠端最新開發分支: $branchName" -ForegroundColor Green
    
    # 切換並拉取最新
    $currentBranch = (git branch --show-current).Trim()
    if ($currentBranch -ne $branchName) {
        git checkout $branchName | Out-Null
    }
    git pull origin $branchName --rebase
} else {
    Write-Host "🎯 正在同步主分支 (main)..." -ForegroundColor Green
    git pull origin main --rebase
}

# 4. 還原先前暫存的本地變更
if ($stashed) {
    Write-Host "🔓 正在還原先前暫存的本地變更 (git stash pop)..." -ForegroundColor Magenta
    git stash pop | Out-Null
}
Write-Host "✅ [軌道 1] Git 程式碼同步完成！" -ForegroundColor Green

# -------------------------------------------------------------------------
# 軌道 2：Google Drive 實體二進位檔案對齊 (.xlsx, .docx, .pdf 等)
# -------------------------------------------------------------------------
Write-Host "`n☁️ [軌道 2/3] 檢查 Google Drive 雲端硬碟二進位備份檔案..." -ForegroundColor Yellow

if (Test-Path $driveBackupRoot) {
    $todayStr = (Get-Date).ToString("yyyyMMdd")
    $yesterdayStr = (Get-Date).AddDays(-1).ToString("yyyyMMdd")
    
    # 尋找最近 48 小時內命名的專案備份資料夾 (例如 20260904_三合一單網頁架機伺服器 或 三合一單自動產生器_20260904_*)
    $backupDirs = Get-ChildItem -Path $driveBackupRoot -Directory | 
        Where-Object { 
            $_.Name -match "^($todayStr|$yesterdayStr)_" -or 
            $_.Name -match "_($todayStr|$yesterdayStr)" -or
            $_.LastWriteTime -ge (Get-Date).AddHours(-48)
        }
    
    if ($backupDirs) {
        foreach ($dir in $backupDirs) {
            $dirName = $dir.Name
            
            # 解析真實子專案名稱 (剝除日期前綴或後綴)
            $cleanName = $dirName -replace "^\d{8}_", "" -replace "_\d{8}(_\d+)?$", ""
            
            # 尋找本地對應的專案目錄
            $targetLocal = Join-Path $projectRoot $cleanName
            if (!(Test-Path $targetLocal)) {
                # 搜尋第一類/第二類/第三類等深層目錄
                $foundDir = Get-ChildItem -Path $projectRoot -Directory -Recurse -Depth 2 -Filter $cleanName -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($foundDir) {
                    $targetLocal = $foundDir.FullName
                }
            }
            
            if (Test-Path $targetLocal) {
                Write-Host "📥 鏡像覆蓋實體二進位檔案: $($dir.Name) -> $cleanName" -ForegroundColor Cyan
                # 使用 robocopy 僅複製較新檔案 (/XO) 或缺失檔案，排除 git 內部檔案
                robocopy $dir.FullName $targetLocal /E /XO /R:1 /W:1 /XD .git node_modules venv .venv /NDL /NFL /NJH /NJS | Out-Null
            }
        }
        Write-Host "✅ [軌道 2] Google Drive 實體二進位檔案對齊完成！" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ [軌道 2] 雲端硬碟最近 48 小時內無獨立專案備份資料夾需要鏡像。" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠️ [軌道 2] 找不到 Google Drive 路徑 ($driveBackupRoot)，略過實體鏡像。" -ForegroundColor DarkYellow
}

# -------------------------------------------------------------------------
# 軌道 3：中央大腦 (%USERPROFILE%\.ai) 全域規則與技能同步
# -------------------------------------------------------------------------
Write-Host "`n🧠 [軌道 3/3] 同步中央大腦 (%USERPROFILE%\.ai)..." -ForegroundColor Yellow

if (Test-Path $aiBrainRoot) {
    Set-Location $aiBrainRoot
    git pull origin main --rebase
    Write-Host "✅ [軌道 3] 中央大腦同步完成！" -ForegroundColor Green
} else {
    Write-Host "⚠️ [軌道 3] 找不到中央大腦路徑 ($aiBrainRoot)，略過。" -ForegroundColor DarkYellow
}

# 返回主專案
Set-Location $projectRoot

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "🎉【三軌合一開工同步】全數順利完成！" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green