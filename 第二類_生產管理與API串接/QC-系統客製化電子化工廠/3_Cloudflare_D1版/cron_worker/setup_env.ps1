# Setup & Deploy script for QC Cron Worker
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "=== 正在檢查 Python 環境並部署 QC 定時排程 Worker ===" -ForegroundColor Cyan
python deploy_cron.py
