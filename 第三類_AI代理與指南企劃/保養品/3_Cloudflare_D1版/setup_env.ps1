$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== AI Skincare Website V8 (Cloudflare Pages + D1 + DeepSeek R1) ===" -ForegroundColor Cyan

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js / npx not found. Please install Node.js LTS first."
    exit 1
}

Write-Host "[1/2] Deploying to Cloudflare Pages (skincare-ai-website)..." -ForegroundColor Yellow
npx wrangler pages deploy public --project-name=skincare-ai-website --commit-dirty=true

Write-Host "[2/2] Done! URL: https://skincare-ai-website.pages.dev" -ForegroundColor Green
