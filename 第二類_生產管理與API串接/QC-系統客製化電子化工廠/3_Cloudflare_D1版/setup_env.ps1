$env:NODE_OPTIONS = "--use-system-ca"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"

# Fix for Node 24 Windows libuv assertion crash: prefer stable Node v22 if available
$node22Dir = "C:\Users\C606\AppData\Local\ms-playwright-go\1.50.1"
if (Test-Path "$node22Dir\node.exe") {
    $env:PATH = "$node22Dir;$env:PATH"
}

$ErrorActionPreference = "Stop"
Write-Host "Deploying QC System to Cloudflare Pages + D1..." -ForegroundColor Cyan

$src = $PSScriptRoot
$stage = Join-Path $env:TEMP "qc_cf_stage"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null

Copy-Item (Join-Path $src "index.html") $stage
if (Test-Path (Join-Path $src "admin.html")) { Copy-Item (Join-Path $src "admin.html") $stage }
if (Test-Path (Join-Path $src "manifest.json")) { Copy-Item (Join-Path $src "manifest.json") $stage }
if (Test-Path (Join-Path $src "sw.js")) { Copy-Item (Join-Path $src "sw.js") $stage }
if (Test-Path (Join-Path $src "xlsx.full.min.js")) { Copy-Item (Join-Path $src "xlsx.full.min.js") $stage }
if (Test-Path (Join-Path $src "icons")) { Copy-Item (Join-Path $src "icons") $stage -Recurse }
if (Test-Path (Join-Path $src "functions")) { Copy-Item (Join-Path $src "functions") $stage -Recurse }
if (Test-Path (Join-Path $src "wrangler.toml")) { Copy-Item (Join-Path $src "wrangler.toml") $stage }

Push-Location $stage
try {
    wrangler pages deploy ./ --project-name="qc-samples" --branch="main" --commit-dirty=true
} finally {
    Pop-Location
}
Write-Host "Deployment completed successfully!" -ForegroundColor Cyan
