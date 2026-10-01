Write-Host "開始將最新版 ChemFlow Pro 部署到 Cloudflare 雲端..." -ForegroundColor Cyan
Write-Host "正在檢查 Cloudflare 登入狀態..." -ForegroundColor Yellow
npx wrangler whoami
if ($LASTEXITCODE -ne 0) {
    Write-Host "尚未登入，將為您開啟瀏覽器進行授權，請在瀏覽器中點擊 Allow..." -ForegroundColor Red
    npx wrangler login
}

Write-Host "正在上傳網頁檔案至 Cloudflare Pages..." -ForegroundColor Yellow
npx wrangler pages deploy public --project-name chemflow-pro

Write-Host "=========================================" -ForegroundColor Green
Write-Host "部署完成！您的最新修改已經正式推上雲端！" -ForegroundColor Green
Write-Host "請按 Enter 鍵關閉此視窗。" -ForegroundColor Green
Read-Host
