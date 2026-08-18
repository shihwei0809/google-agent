# ==========================================
# Google Apps Script (clasp) 一鍵環境設定腳本
# ==========================================

Write-Host "開始檢查與設定開發環境..." -ForegroundColor Cyan

# 1. 檢查並安裝 Node.js
try {
    $nodeVersion = node -v
    Write-Host "已安裝 Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "未偵測到 Node.js，準備下載安裝..." -ForegroundColor Yellow
    # 使用 winget 安裝 Node.js
    winget install OpenJS.NodeJS
    Write-Host "Node.js 安裝指令已送出，請依畫面指示完成安裝，完成後可能需要重新啟動終端機。" -ForegroundColor Yellow
}

# 2. 檢查並安裝 @google/clasp
try {
    $claspVersion = clasp -v
    Write-Host "已安裝 clasp: $claspVersion" -ForegroundColor Green
} catch {
    Write-Host "未偵測到 @google/clasp，開始安裝..." -ForegroundColor Yellow
    npm install -g @google/clasp
    Write-Host "@google/clasp 安裝完成！" -ForegroundColor Green
}

Write-Host ""
Write-Host "環境設定完成！" -ForegroundColor Cyan
Write-Host "若您尚未登入 clasp，請在終端機輸入以下指令進行登入：" -ForegroundColor Yellow
Write-Host "clasp login" -ForegroundColor White
Write-Host ""
Write-Host "要拉取專案程式碼，請進入 src 資料夾並輸入：" -ForegroundColor Yellow
Write-Host "clasp clone <您的_Script_ID>" -ForegroundColor White
Write-Host "=========================================="
Pause
