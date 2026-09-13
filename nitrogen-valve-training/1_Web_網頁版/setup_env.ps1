# =====================================================================
# 🚀 儲槽氮氣閥教育訓練系統環境一鍵設定腳本 (setup_env.ps1)
# =====================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎨 開始檢查並安裝「儲槽氮氣閥教育訓練系統」環境..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. 檢查並配置 Python 與依賴
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✓ 偵測到 Python，開始安裝依賴套件 (Pillow, edge-tts)..." -ForegroundColor Green
    python -m pip install --upgrade pip
    python -m pip install Pillow edge-tts
    Write-Host "✓ Python 依賴安裝完成！" -ForegroundColor Green
} else {
    Write-Warning "⚠️ 未在系統中偵測到 Python。如需重新生成簡報圖片或語音旁白，請先安裝 Python 3！"
}

# 2. 檢查並配置 Node.js 與 Netlify CLI
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "✓ 偵測到 Node.js，開始檢查/安裝 Netlify 部署工具..." -ForegroundColor Green
    npm install -g netlify-cli
    Write-Host "✓ Netlify CLI 安裝完成！" -ForegroundColor Green
    
    # 連結本機至 Netlify 專案
    Write-Host "✓ 開始進行 Netlify 專案連結配置..." -ForegroundColor Green
    npx netlify link --id ff147b6f-9324-47c8-acc0-d46952d0c205
    Write-Host "✓ 連結配置完成！" -ForegroundColor Green
} else {
    Write-Warning "⚠️ 未在系統中偵測到 Node.js (npm)。如需發佈線上網址，請先安裝 Node.js！"
}

Write-Host "`n🎉 環境設定檢查結束！您現在可以開始開發、執行或發佈專案了。" -ForegroundColor Cyan
