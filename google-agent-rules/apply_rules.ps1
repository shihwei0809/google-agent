# =====================================================================
# 🚀 複製並套用 AI 規則至此電腦的全域配置中 (apply_rules.ps1)
# =====================================================================

$GlobalConfigDir = "$Home\.gemini\config"
if (!(Test-Path $GlobalConfigDir)) {
    New-Item -ItemType Directory -Force -Path $GlobalConfigDir
}

$DestPath = "$GlobalConfigDir\AGENTS.md"
Copy-Item -Path "AGENTS.md" -Destination $DestPath -Force

Write-Host "==================================================" -ForegroundColor Green
Write-Host "✓ 成功套用今日 AI 規則至此電腦的全域設定檔中！" -ForegroundColor Green
Write-Host "路徑: $DestPath" -ForegroundColor Green
Write-Host "往後在此電腦任何地方執行 AI 助理，都將遵循此一鍵安裝規範！" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
