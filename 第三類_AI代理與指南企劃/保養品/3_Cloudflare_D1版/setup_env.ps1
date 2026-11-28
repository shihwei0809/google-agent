$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== AI Skincare Website V8 (Cloudflare Pages + D1 + DeepSeek R1) ===" -ForegroundColor Cyan

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js / npx not found. Please install Node.js LTS first."
    exit 1
}

Write-Host "[1/2] Deploying to Cloudflare Pages (skincare-ai-website)..." -ForegroundColor Yellow
$tmp = Join-Path $env:TEMP "skincare_deploy"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Copy-Item $PSScriptRoot $tmp -Recurse
try {
    Set-Location $tmp
    npx wrangler pages deploy public --project-name=skincare-ai-website --branch=main --commit-dirty=true
} finally {
    Set-Location $PSScriptRoot
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
}

Write-Host "[2/2] Done! URL: https://skincare-ai-website.pages.dev" -ForegroundColor Green
