$env:CLOUDFLARE_API_TOKEN = $null
$env:CLOUDFLARE_ACCOUNT_ID = $null
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"

# Fix for Node 24 Windows libuv assertion crash: prefer stable Node v22 if available
$node22Dir = "C:\Users\C606\AppData\Local\ms-playwright-go\1.50.1"
if (Test-Path "$node22Dir\node.exe") {
    $env:PATH = "$node22Dir;$env:PATH"
}

$ErrorActionPreference = "Stop"
Write-Host "Deploying QC System to Cloudflare Pages + D1..." -ForegroundColor Cyan

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Node.js (npx) not found" -ForegroundColor Red
    exit 1
}

$d1_list = npx wrangler d1 list
if ($d1_list -match "qc-db") {
    Write-Host "D1 Database (qc-db) already exists." -ForegroundColor Green
} else {
    Write-Host "Creating new D1 Database (qc-db)..." -ForegroundColor Yellow
    npx wrangler d1 create qc-db
}

# The ID is a4cbfe74-f067-462b-b70a-be242f9fafb9
$db_id = "a4cbfe74-f067-462b-b70a-be242f9fafb9"
Write-Host "Found Database ID: $db_id" -ForegroundColor Green

$toml_path = "wrangler.toml"
$toml_content = Get-Content $toml_path -Raw
$toml_content = $toml_content -replace 'database_id\s*=\s*".*"', ('database_id = "' + $db_id + '"')
Set-Content $toml_path -Value $toml_content -Encoding UTF8

# npx wrangler d1 execute qc-db --remote --file=schema.sql
npx wrangler pages deploy ./ --project-name="qc-samples" --branch="main" --commit-dirty=true
Write-Host "Deployment completed successfully!" -ForegroundColor Cyan
