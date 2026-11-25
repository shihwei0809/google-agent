$ErrorActionPreference = "Continue"
Write-Host "資材辦公室 2D/3D 互動平面配置工具 - 環境檢測" -ForegroundColor Cyan
if (Get-Command python -ErrorAction SilentlyContinue) {
    python -c "import docx" 2>$null
    if ($LASTEXITCODE -ne 0) { python -m pip install python-docx -q }
}
Write-Host "就緒！請雙擊「點我開啟資材辦公室2D3D配置工具.bat」開啟。" -ForegroundColor Green
