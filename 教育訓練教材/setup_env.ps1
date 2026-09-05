<#
.SYNOPSIS
一鍵部署 AI 教育訓練平台環境
#>

$ErrorActionPreference = "Stop"
Write-Host "開始配置 AI 教育訓練平台環境..." -ForegroundColor Cyan

$baseDir = $PSScriptRoot

# 1. 建立並設定後端環境
Write-Host "正在設定後端 (Python FastAPI) 環境..." -ForegroundColor Yellow
$backendDir = Join-Path $baseDir "backend"
if (-not (Test-Path $backendDir)) {
    New-Item -ItemType Directory -Path $backendDir | Out-Null
}
Set-Location $backendDir

if (-not (Test-Path "venv")) {
    Write-Host "建立 Python 虛擬環境..."
    python -m venv venv
}

Write-Host "安裝後端套件..."
$pipCommand = ".\venv\Scripts\pip.exe"
if (Test-Path "requirements.txt") {
    & $pipCommand install -r requirements.txt
} else {
    & $pipCommand install fastapi uvicorn google-generativeai pydantic python-dotenv python-multipart
    & $pipCommand freeze > requirements.txt
}

# 2. 建立並設定前端環境
Write-Host "正在設定前端 (React + Vite) 環境..." -ForegroundColor Yellow
$frontendDir = Join-Path $baseDir "frontend"
if (-not (Test-Path $frontendDir)) {
    Write-Host "初始化 Vite React 專案..."
    Set-Location $baseDir
    npm create vite@latest frontend -- --template react
}

Set-Location $frontendDir
Write-Host "安裝前端套件..."
npm install
npm install tailwindcss postcss autoprefixer axios react-router-dom lucide-react
npm exec tailwindcss init -p

Write-Host "環境配置完成！" -ForegroundColor Green
Write-Host "請依照 README.md 的說明啟動前後端服務。" -ForegroundColor Cyan
Set-Location $baseDir
