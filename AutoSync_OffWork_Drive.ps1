# C:\GOOGLE ANGET\AutoSync_OffWork_Drive.ps1
# 自動偵測今天有修改過的檔案與子專案，並精確備份至 Google Drive 專案備份目錄

$srcRoot = "C:\GOOGLE ANGET"
$destRoot = "G:\我的雲端硬碟\GOOGLE ANGET\專案備份"

# 確保備份根目錄存在
if (!(Test-Path -Path $destRoot)) {
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
}

Write-Host "🔍 [自動備份] 正在掃描最近 24 小時內修改過的檔案與專案..." -ForegroundColor Yellow

# 1. 抓取最近 24 小時內修改過的檔案 (排除 node_modules, venv, .git, .netlify, .wrangler, .firebase)
$modifiedFiles = Get-ChildItem -Path $srcRoot -Recurse -File -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.LastWriteTime -ge (Get-Date).AddDays(-1) -and 
        $_.FullName -notmatch "node_modules" -and 
        $_.FullName -notmatch "venv" -and 
        $_.FullName -notmatch "\\.git" -and
        $_.FullName -notmatch "\\.netlify" -and
        $_.FullName -notmatch "\\.wrangler" -and
        $_.FullName -notmatch "\\.firebase"
    }

if (!$modifiedFiles) {
    Write-Host "✅ [自動備份] 今日無檔案修改，無須備份。" -ForegroundColor Green
    exit 0
}

# 2. 遍歷並記錄需要被備份的專案目錄或獨立檔案
$copiedItems = @()

foreach ($file in $modifiedFiles) {
    $fullName = $file.FullName
    $relPath = $fullName.Substring($srcRoot.Length + 1)
    $parts = $relPath.Split([System.IO.Path]::DirectorySeparatorChar)
    
    # 情況 A：如果是根目錄下的獨立檔案 (例如 bat_launcher_template.bat, HANDOVER.md)
    if ($parts.Length -eq 1) {
        if ($copiedItems -notcontains $fullName) {
            Copy-Item -Path $fullName -Destination $destRoot -Force
            $copiedItems += $fullName
            Write-Host "💾 [自動備份] 複製根目錄變更檔案: $relPath" -ForegroundColor Green
        }
    } else {
        # 情況 B：如果是子目錄下的專案
        $category = $parts[0]
        
        # 判定是否在「第一類」、「第二類」、「第三類」、「說明書」等類別目錄下
        if ($category -in @("第一類_核心網頁與互動系統", "第二類_生產管理與API串接", "第三類_AI代理與指南企劃", "說明書")) {
            if ($parts.Length -gt 1) {
                $subFolder = Join-Path $category $parts[1]
                $srcFolder = Join-Path $srcRoot $subFolder
                $destFolder = Join-Path $destRoot $parts[1]
                
                if ($copiedItems -notcontains $srcFolder) {
                    if (Test-Path -Path $srcFolder -PathType Container) {
                        Write-Host "💾 [自動備份] 複製已修改子專案: $subFolder -> 專案備份\\$($parts[1])" -ForegroundColor Cyan
                        robocopy $srcFolder $destFolder /E /R:1 /W:1 /XD .git node_modules venv .venv .netlify .wrangler .firebase /XF *.zip /NDL /NFL /NJH /NJS | Out-Null
                        $copiedItems += $srcFolder
                    }
                }
            }
        } else {
            # 其他一般第一層子目錄下的專案 (例如 flowchart-web, ai-voice-cloner-guide)
            $srcFolder = Join-Path $srcRoot $category
            $destFolder = Join-Path $destRoot $category
            
            if ($copiedItems -notcontains $srcFolder) {
                if (Test-Path -Path $srcFolder -PathType Container) {
                    Write-Host "💾 [自動備份] 複製已修改專案: $category -> 專案備份\\$category" -ForegroundColor Cyan
                    robocopy $srcFolder $destFolder /E /R:1 /W:1 /XD .git node_modules venv .venv .netlify .wrangler .firebase /XF *.zip /NDL /NFL /NJH /NJS | Out-Null
                    $copiedItems += $srcFolder
                }
            }
        }
    }
}

Write-Host "🎉 [自動備份] 備份同步完成！" -ForegroundColor Green
