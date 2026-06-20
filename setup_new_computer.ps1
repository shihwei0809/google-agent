# Anti-Gravity 跨電腦一鍵同步與環境初始化腳本 (setup_new_computer.ps1)
# 語系：繁體中文 (Taiwan)
# 執行方式：在 Windows PowerShell 視窗中執行：PowerShell.exe -ExecutionPolicy Bypass -File .\setup_new_computer.ps1

$ErrorActionPreference = "SilentlyContinue"
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 Anti-Gravity 跨電腦自動化環境部署與同步工具" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "正在為你偵測與同步此電腦的開發環境與授權設定..." -ForegroundColor Yellow

# 1. 偵測當前環境變數
$currentUsername = $env:USERNAME
$userProfile = $env:USERPROFILE
$currentFolder = Get-Location

Write-Host "當前電腦使用者名稱: $currentUsername" -ForegroundColor Gray
Write-Host "工作目錄: $currentFolder" -ForegroundColor Gray

# 2. 自動檢查並透過 Windows winget 安裝必要相依軟體
function Install-NeedTool {
    param (
        [string]$Name,
        [string]$Command,
        [string]$WingetId
    )
    
    $check = Get-Command $Command -ErrorAction SilentlyContinue
    if ($check) {
        Write-Host "✅ $Name 已安裝，版本: $(& $Command --version 2>&1 | Select-Object -First 1)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 偵測到未安裝 $Name，正在使用 Windows Winget 背景安裝..." -ForegroundColor Yellow
        winget install --id $WingetId -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            Write-Host "🎉 $Name 安裝成功！" -ForegroundColor Green
        } else {
            Write-Host "❌ $Name 安裝失敗，請稍後手動至官網下載安裝。" -ForegroundColor Red
        }
    }
}

# 安裝基本相依工具
Install-NeedTool -Name "Git" -Command "git" -WingetId "Git.Git"
Install-NeedTool -Name "GitHub CLI" -Command "gh" -WingetId "GitHub.cli"
Install-NeedTool -Name "Node.js" -Command "node" -WingetId "OpenJS.NodeJS"
Install-NeedTool -Name "Python" -Command "python" -WingetId "Python.Python.3.12"

# 3. 安裝 Obsidian MCP 工具 (MCPVault)
Write-Host "`n📦 正在檢查並配置 Obsidian MCP (MCPVault)..." -ForegroundColor Yellow
$mcpVaultCheck = Get-Command "mcpvault" -ErrorAction SilentlyContinue
if ($mcpVaultCheck) {
    Write-Host "✅ MCPVault 已安裝。" -ForegroundColor Green
} else {
    Write-Host "正在透過 npm 全域安裝 @bitbonsai/mcpvault..." -ForegroundColor Yellow
    npm.cmd install -g @bitbonsai/mcpvault | Out-Null
    if (Get-Command "mcpvault" -ErrorAction SilentlyContinue) {
        Write-Host "🎉 MCPVault 安裝成功！" -ForegroundColor Green
    } else {
        Write-Host "❌ MCPVault 安裝失敗，請確認 npm 網路狀態。" -ForegroundColor Red
    }
}

# 4. 安裝 NotebookLM MCP 與簡報生成必備 Python 庫
Write-Host "`n📦 正在安裝 NotebookLM MCP 與簡報生成必備 Python 庫 (python-pptx)..." -ForegroundColor Yellow
pip install notebooklm-mcp-cli python-pptx --quiet
if (Get-Command "nlm" -ErrorAction SilentlyContinue) {
    Write-Host "✅ NotebookLM CLI (nlm) 安裝就緒。" -ForegroundColor Green
} else {
    Write-Host "❌ NotebookLM CLI 安裝失敗，請確認 pip 是否正常運作。" -ForegroundColor Red
}

# 5. 自動配置新電腦的 Anti-Gravity MCP 設定檔
Write-Host "`n⚙️ 正在自動注入與同步 Anti-Gravity MCP 設定檔..." -ForegroundColor Yellow

# 定位當前 Google Drive 下的 Obsidian Vault 實體路徑（優先尋找 Google Drive 內的路徑）
$obsidianVaultPath = "G:\我的雲端硬碟\Secondbrain"
if (-not (Test-Path $obsidianVaultPath)) {
    $obsidianVaultPath = "G:\我的雲端硬碟\Obsidian"
    if (-not (Test-Path $obsidianVaultPath)) {
        $obsidianVaultPath = Join-Path $userProfile "OneDrive\文件\Secondbrain"
    }
}

$mcpVaultCmdPath = "$userProfile\AppData\Roaming\npm\mcpvault.cmd"

# 定義我們要注入的 MCP 伺服器設定結構 (支援 mcpServers 與 mcp 兩種常見 Key 名稱，確保 100% 相容)
$mcpServersConfig = @{
    "obsidian" = @{
        "command" = $mcpVaultCmdPath
        "args" = @($obsidianVaultPath)
    }
    "notebooklm" = @{
        "command" = "nlm"
        "args" = @("mcp")
    }
    "firebase" = @{
        "command" = "npx.cmd"
        "args" = @("-y", "firebase-tools@latest", "mcp")
    }
}

# 備用的 mcp 格式結構 (部分舊版或特定 Client 支援)
$mcpCompatConfig = @{
    "obsidian" = @{
        "type" = "local"
        "command" = @($mcpVaultCmdPath, $obsidianVaultPath)
        "enabled" = $true
    }
    "notebooklm" = @{
        "type" = "local"
        "command" = @("nlm", "mcp")
        "enabled" = $true
    }
    "firebase" = @{
        "type" = "local"
        "command" = @("npx.cmd", "-y", "firebase-tools@latest", "mcp")
        "enabled" = $true
    }
}

# 設定檔儲存目錄
$agConfigDir = Join-Path $userProfile ".gemini\antigravity"
if (-not (Test-Path $agConfigDir)) {
    New-Item -ItemType Directory -Path $agConfigDir -Force | Out-Null
}

# 我們會將設定寫入三個可能的設定檔名，以確保編輯器能讀取到
$configFiles = @("mcp_config.json", "config.json", "settings.json")

foreach ($fileName in $configFiles) {
    $filePath = Join-Path $agConfigDir $fileName
    $existingData = @{}
    
    if (Test-Path $filePath) {
        # 讀取現有的設定檔內容，避免覆蓋使用者其他的個人化設定 (如主題、快速鍵)
        try {
            $rawContent = Get-Content -Path $filePath -Raw -Encoding utf8
            if ($rawContent) {
                $existingData = $rawContent | ConvertFrom-Json -AsHashtable
            }
        } catch {
            Write-Host "讀取舊設定檔 $fileName 時發生解析錯誤，將重新生成。" -ForegroundColor Gray
        }
    }
    
    # 進行 JSON 合併
    if (-not $existingData) { $existingData = @{} }
    
    # 注入標準 mcpServers 區塊
    $existingData["mcpServers"] = $mcpServersConfig
    # 注入相容的 mcp 區塊
    $existingData["mcp"] = $mcpCompatConfig
    
    # 重新序列化回 JSON 檔案
    try {
        $updatedJson = $existingData | ConvertTo-Json -Depth 10
        $updatedJson | Out-File -FilePath $filePath -Encoding utf8 -Force
        Write-Host "✅ 已成功配置/合併至: $filePath" -ForegroundColor Green
    } catch {
        Write-Host "❌ 寫入設定檔 $fileName 失敗！" -ForegroundColor Red
    }
}

# 5.5 從 Google Drive 備份中還原自訂技能與設定 (一鍵還原/轉移)
Write-Host "`n🔄 正在檢查是否有 Google Drive 技能備份以進行自動還原..." -ForegroundColor Yellow
$gdriveName = [string][char]0x6211 + [char]0x7684 + [char]0x96f2 + [char]0x7aef + [char]0x786c + [char]0x789f
$gdrivePath = "G:\$gdriveName\GOOGLE ANGET"
$backupSrc = Join-Path $gdrivePath "backup"

if (Test-Path $backupSrc) {
    # 還原全域設定 (config)
    $backupConfig = Join-Path $backupSrc "config"
    if (Test-Path $backupConfig) {
        $localConfigDir = Join-Path $userProfile ".gemini\config"
        if (-not (Test-Path $localConfigDir)) {
            New-Item -ItemType Directory -Path $localConfigDir -Force | Out-Null
        }
        Copy-Item -Path "$backupConfig\*" -Destination $localConfigDir -Recurse -Force
        Write-Host "🎉 成功還原全域設定與授權檔！" -ForegroundColor Green
    }
    
    # 還原 Antigravity 提示詞技能
    $backupAGSkills = Join-Path $backupSrc "antigravity\skills"
    if (Test-Path $backupAGSkills) {
        $localAGSkills = Join-Path $userProfile ".gemini\antigravity\skills"
        if (-not (Test-Path $localAGSkills)) {
            New-Item -ItemType Directory -Path $localAGSkills -Force | Out-Null
        }
        Copy-Item -Path "$backupAGSkills\*" -Destination $localAGSkills -Recurse -Force
        Write-Host "🎉 成功還原 Antigravity 提示詞技能！" -ForegroundColor Green
    }
    
    # 還原 Antigravity 使用者設定
    $backupAGSettings = Join-Path $backupSrc "antigravity\user_settings.pb"
    if (Test-Path $backupAGSettings) {
        $localAGSettings = Join-Path $userProfile ".gemini\antigravity\user_settings.pb"
        Copy-Item -Path $backupAGSettings -Destination $localAGSettings -Force
        Write-Host "🎉 成功還原 Antigravity 使用者授權設定！" -ForegroundColor Green
    }

    # 還原本機工作區技能
    $backupWorkspaceSkills = Join-Path $backupSrc "workspace_skills"
    if (Test-Path $backupWorkspaceSkills) {
        $localWorkspaceSkills = "C:\GOOGLE ANGET\skills"
        if (-not (Test-Path $localWorkspaceSkills)) {
            New-Item -ItemType Directory -Path $localWorkspaceSkills -Force | Out-Null
        }
        Copy-Item -Path "$backupWorkspaceSkills\*" -Destination $localWorkspaceSkills -Recurse -Force
        Write-Host "🎉 成功還原工作區自訂技能！" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️ 找不到雲端備份目錄，跳過自動還原。" -ForegroundColor Gray
}

# 6. 一鍵引導所有必要服務登入流程
Write-Host "`n🔑 正在開啟外部帳號授權流程，請於彈出視窗中完成登入：" -ForegroundColor Yellow

# GitHub
Write-Host "👉 正在驗證 GitHub..." -ForegroundColor Cyan
gh auth login --web --git-protocol https

# Firebase
Write-Host "👉 正在驗證 Firebase..." -ForegroundColor Cyan
npx.cmd -y firebase-tools@latest login

# NotebookLM
Write-Host "👉 正在驗證 NotebookLM..." -ForegroundColor Cyan
nlm login

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "🎉 此電腦的 Anti-Gravity 同步與初始化全部完成！" -ForegroundColor Cyan
Write-Host "請重新啟動 Anti-Gravity 以套用全新設定。" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Read-Host "按下任意鍵結束..."
