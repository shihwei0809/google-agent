$drives = Get-PSDrive -PSProvider FileSystem | Select-Object -ExpandProperty Name
$gDrivePath = ""
foreach ($drive in $drives) {
    $testPath = $drive + ":\我的雲端硬碟\GOOGLE ANGET\專案備份"
    if (Test-Path $testPath) {
        $gDrivePath = $testPath
        break
    }
}

if (-not $gDrivePath) {
    $gDrivePath = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份"
    New-Item -ItemType Directory -Force -Path $gDrivePath | Out-Null
}

$today = (Get-Date).ToString("yyyyMMdd")
$snapshotDir = Join-Path $gDrivePath "00_最近7天收工快照\($today)_收工備份"
New-Item -ItemType Directory -Force -Path $snapshotDir | Out-Null

Write-Host "開始執行 Robocopy 異動備份至: $snapshotDir"
robocopy "d:\GOOGLE ANGET" $snapshotDir /S /MAXAGE:$today /XD ".git" "node_modules" ".wrangler" | Out-String

$recentDir = Join-Path $gDrivePath "00_最近7天收工快照"
$folders = Get-ChildItem -Path $recentDir -Directory
foreach ($folder in $folders) {
    if ($folder.CreationTime -lt (Get-Date).AddDays(-7)) {
        $monthDir = Join-Path $gDrivePath "01_歷史按月封存\"
        New-Item -ItemType Directory -Force -Path $monthDir | Out-Null
        $dest = Join-Path $monthDir $folder.Name
        Write-Host "封存超過 7 天的備份: $(.Name) -> $monthDir"
        Move-Item -Path $folder.FullName -Destination $dest -Force
    }
}
Write-Host "備份與封存流程完成！"
