# Cloudflare Pages + D1 Auto Setup Script
Write-Host "========================================="
Write-Host " EGUPS System - Cloudflare D1 Deployment "
Write-Host "========================================="

if (!(Get-Command "npx" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: npx not found. Please install Node.js!" -ForegroundColor Red
    exit
}

$env:NODE_OPTIONS='--dns-result-order=ipv4first'
Write-Host "1. Logging into Cloudflare..." -ForegroundColor Cyan
if (-not $env:CLOUDFLARE_API_TOKEN) { npx wrangler login } else { Write-Host "Using CLOUDFLARE_API_TOKEN from environment." -ForegroundColor Green }

Write-Host "`n2. Creating D1 database (egups-db)..." -ForegroundColor Cyan
$d1Output = npx wrangler d1 create egups-db | Out-String

$dbId = ""
if ($d1Output -match 'database_id = "([^"]+)"') {
    $dbId = $matches[1]
} elseif ($d1Output -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') {
    $dbId = $matches[1]
}

if ($dbId) {
    Write-Host "Success! D1 DB ID: $dbId" -ForegroundColor Green
    
    $tomlPath = "wrangler.toml"
    $tomlContent = Get-Content $tomlPath -Raw
    $tomlContent = $tomlContent -replace 'database_id = ""', "database_id = `"$dbId`""
    Set-Content $tomlPath $tomlContent -Encoding UTF8
    Write-Host "Updated wrangler.toml automatically." -ForegroundColor Green
} else {
    Write-Host "Warning: Could not extract database_id. It might already exist." -ForegroundColor Yellow
}

Write-Host "`n3. Executing schema.sql..." -ForegroundColor Cyan
npx wrangler d1 execute egups-db --file=./schema.sql --remote -y

Write-Host "`n4. Deploying to Cloudflare Pages..." -ForegroundColor Cyan
npx wrangler pages deploy public --project-name=egups-system

Write-Host "`n========================================="
Write-Host " Deployment Completed! " -ForegroundColor Green
Write-Host "========================================="



