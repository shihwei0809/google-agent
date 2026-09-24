# setup_env.ps1
# Setup script for Cloudflare Pages + D1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " IPA System - Cloudflare Serverless Deployment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "Error: npm not found. Please install Node.js!" -ForegroundColor Red
    Exit
}

# 🛠 強制清除當前視窗的 API Token 環境變數，強迫走瀏覽器 OAuth 登入
if ($env:CLOUDFLARE_API_TOKEN) {
    Write-Host "Clearing old CLOUDFLARE_API_TOKEN from this session..." -ForegroundColor Yellow
    Remove-Item Env:\CLOUDFLARE_API_TOKEN -ErrorAction SilentlyContinue
}

Write-Host "Installing Cloudflare Wrangler CLI..." -ForegroundColor Yellow
npm install -g wrangler

Write-Host "Logging into Cloudflare..." -ForegroundColor Yellow
npx wrangler login

Write-Host "Creating D1 database (ipa-pwa-db)..." -ForegroundColor Yellow
$d1Output = npx wrangler d1 create ipa-pwa-db | Out-String

$dbId = ""
if ($d1Output -match 'database_id = "(.*?)"') {
    $dbId = $matches[1]
    Write-Host "Success! Database ID: $dbId" -ForegroundColor Green
    
    $tomlPath = ".\wrangler.toml"
    $tomlContent = Get-Content $tomlPath
    $newTomlContent = $tomlContent -replace 'database_id = ".*?"', "database_id = `"$dbId`""
    Set-Content -Path $tomlPath -Value $newTomlContent -Encoding UTF8
    Write-Host "wrangler.toml updated automatically." -ForegroundColor Green
} else {
    Write-Host "❌ Error: Could not parse Database ID or creation failed." -ForegroundColor Red
    Write-Host $d1Output
    Exit
}

Write-Host "Initializing database schema..." -ForegroundColor Yellow
npx wrangler d1 execute ipa-pwa-db --local --file=./schema.sql
npx wrangler d1 execute ipa-pwa-db --remote --file=./schema.sql

Write-Host "Deploying to Cloudflare Pages..." -ForegroundColor Yellow
npx wrangler pages deploy public --project-name ipa-pwa-app

Write-Host "Deployment completed!" -ForegroundColor Green
