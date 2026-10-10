$ErrorActionPreference = 'SilentlyContinue'
$Today = Get-Date -Format "yyyyMMdd"
$BackupFolderName = "${Today}_收工備份"

# Find Google Drive
$DriveLetters = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 -or $_.DriveType -eq 4 } | Select-Object -ExpandProperty DeviceID
$GdriveRoot = $null
foreach ($letter in $DriveLetters) {
    if (Test-Path "$letter\我的雲端硬碟") {
        $GdriveRoot = "$letter\我的雲端硬碟"
        break
    } elseif (Test-Path "$letter\My Drive") {
        $GdriveRoot = "$letter\My Drive"
        break
    }
}

Write-Output "--- 本機備份紀錄 ---"
if ($null -ne $GdriveRoot) {
    $BackupPath = "$GdriveRoot\GOOGLE ANGET\專案備份\00_最近7天收工快照\$BackupFolderName"
    Write-Output "開始備份至: $BackupPath"
    
    if (-not (Test-Path $BackupPath)) {
        New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null
    }
    
    # 根據 INSTRUCTIONS.md 備份
    $RobocopyOutput = robocopy "C:\GOOGLE ANGET\回收液入料記錄" "$BackupPath\回收液入料記錄" /E /XD .wrangler node_modules .git __pycache__ data /XF *.sqlite *.sqlite-wal *.sqlite-shm *.pyc /R:0 /W:0
    Write-Output $RobocopyOutput
    Write-Output "備份完成"
} else {
    Write-Output "找不到 Google Drive 掛載磁碟"
}
Write-Output "--------------------"

# Git
Write-Output "--- Git 處理紀錄 ---"
cd "C:\GOOGLE ANGET"

# Add and Commit
git add .
git add -f "回收液入料記錄\*.docx" "回收液入料記錄\*.pdf" 2>$null
git commit -m "feat(回收液入料記錄): 驗收完畢，發布上線 - $Today"

# Upgrade Tag
$LatestTag = git describe --tags --abbrev=0 2>$null
if (-not $LatestTag) {
    $NewTag = "v1.0.0"
} else {
    if ($LatestTag -match "v(\d+)\.(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = [int]$matches[3] + 1
        $NewTag = "v$major.$minor.$patch"
    } else {
        $NewTag = $LatestTag + ".1"
    }
}

git tag $NewTag
git push origin main
git push origin $NewTag

$CommitHash = git rev-parse --short HEAD
Write-Output "Git Push 完成: 分支=main, Hash=$CommitHash, Tag=$NewTag"
Write-Output "--------------------"
