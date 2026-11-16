# ============================================================
# blender_3d_demo 一鍵環境設定與初始化腳本 (setup_env.ps1)
# ============================================================
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host "`n=== [1/5] 檢查 Python 與必要套件 ===" -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[錯誤] 找不到 Python，請先安裝 Python 3.9+ 並勾選 Add Python to PATH。" -ForegroundColor Red
    Start-Process "https://www.python.org/downloads/"
    exit 1
}
python -m pip install --upgrade pip -q
python -m pip install python-docx pillow playwright -q
Write-Host "[OK] Python 套件 (python-docx, pillow, playwright) 已就緒。" -ForegroundColor Green

Write-Host "`n=== [2/5] 檢查 Astral uv / uvx ===" -ForegroundColor Cyan
$uvxPath = Join-Path $env:USERPROFILE ".local\bin\uvx.exe"
if (-not (Test-Path $uvxPath) -and -not (Get-Command uvx -ErrorAction SilentlyContinue)) {
    Write-Host "正在安裝 uv..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
} else {
    Write-Host "[OK] uvx 已安裝：$uvxPath" -ForegroundColor Green
}

Write-Host "`n=== [3/5] 檢查 Blender 主程式 ===" -ForegroundColor Cyan
$blenderExe = $null
if (Test-Path "C:\Program Files\Blender Foundation") {
    $blenderExe = Get-ChildItem "C:\Program Files\Blender Foundation" -Recurse -Filter "blender.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $blenderExe) {
    Write-Host "未偵測到 Blender，正在透過 winget 安裝 Blender..." -ForegroundColor Yellow
    winget install --id BlenderFoundation.Blender -e --accept-package-agreements --accept-source-agreements
    $blenderExe = Get-ChildItem "C:\Program Files\Blender Foundation" -Recurse -Filter "blender.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if ($blenderExe) {
    Write-Host "[OK] 找到 Blender：$blenderExe" -ForegroundColor Green
} else {
    Write-Host "[警告] 找不到 blender.exe，請手動安裝後重試。" -ForegroundColor Yellow
}

Write-Host "`n=== [4/5] 安裝並啟用 Blender MCP 外掛 ===" -ForegroundColor Cyan
$addonFile = Join-Path $PSScriptRoot "blender_mcp_addon.py"
if (-not (Test-Path $addonFile)) {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ahujasid/blender-mcp/main/addon.py" -OutFile $addonFile
}
if ($blenderExe -and (Test-Path $addonFile)) {
    $expr = "import bpy; bpy.ops.preferences.addon_install(filepath=r'$addonFile', overwrite=True); bpy.ops.preferences.addon_enable(module='blender_mcp_addon'); bpy.ops.wm.save_userpref(); print('MCP_ADDON_READY')"
    & $blenderExe -b --python-expr $expr
}

Write-Host "`n=== [5/5] 生成圖文操作手冊 (.docx) ===" -ForegroundColor Cyan
if (Test-Path (Join-Path $PSScriptRoot "build_manual_doc.py")) {
    python (Join-Path $PSScriptRoot "build_manual_doc.py")
}

Write-Host "`n環境設定完成！請雙擊 啟動3D儲位展示.bat 開始使用。" -ForegroundColor Green
