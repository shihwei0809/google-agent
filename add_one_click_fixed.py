import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the broken part
import re
html = re.sub(r'const deployPsCode = `\\Continue =.*?const batShortcutCode = ', 'const batShortcutCode = ', html, flags=re.DOTALL)

deploy_ps_code = '''
const deployPsCode = `\\$ErrorActionPreference = "Stop"
\\$projectName = Read-Host "請輸入要建立的專案英文名稱 (例如: my-training-app，不可包含中文或空格)"
if (-not \\$projectName) { Write-Host "名稱不可為空！" -ForegroundColor Red; exit }

Write-Host "\\n[1/4] 正在建立 D1 資料庫 (\\$projectName)..." -ForegroundColor Cyan
\\$d1Output = npx wrangler d1 create \\$projectName | Out-String
Write-Host \\$d1Output

\\$dbIdMatch = [regex]::Match(\\$d1Output, 'database_id\\s*=\\s*"([^"]+)"')
if (-not \\$dbIdMatch.Success) {
    Write-Host "無法自動擷取 database_id，請確認您已登入 Wrangler (npx wrangler login)！" -ForegroundColor Red
    exit
}
\\$dbId = \\$dbIdMatch.Groups[1].Value
Write-Host "成功獲取資料庫 ID: \\$dbId" -ForegroundColor Green

Write-Host "\\n[2/4] 正在自動更新 wrangler.toml..." -ForegroundColor Cyan
\\$tomlPath = Join-Path \\$PSScriptRoot "wrangler.toml"
\\$tomlContent = Get-Content -Path \\$tomlPath -Raw
\\$tomlContent = \\$tomlContent -replace 'database_name\\s*=\\s*".*?"', "database_name = \\"\\$projectName\\""
\\$tomlContent = \\$tomlContent -replace 'database_id\\s*=\\s*".*?"', "database_id = \\"\\$dbId\\""
Set-Content -Path \\$tomlPath -Value \\$tomlContent -Encoding UTF8
Write-Host "wrangler.toml 更新完成！" -ForegroundColor Green

Write-Host "\\n[3/4] 正在將資料表結構 (schema.sql) 寫入雲端 D1 資料庫..." -ForegroundColor Cyan
npx wrangler d1 execute \\$projectName --remote --file=./schema.sql

Write-Host "\\n[4/4] 正在將網站發布至 Cloudflare Pages..." -ForegroundColor Cyan
npx wrangler pages deploy . --project-name \\$projectName

Write-Host "\\n========================================================" -ForegroundColor Green
Write-Host "🎉 部署完成！您的網站與資料庫已成功上線！" -ForegroundColor Green
Write-Host "請注意上面的 Pages URL 即可開始測試您的教育訓練系統。" -ForegroundColor Green
`;

const deployBatCode = `@echo off
chcp 65001 >nul
echo ========================================================
echo   Cloudflare Pages + D1 雲端資料庫 自動化部署工具
echo ========================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"
pause
`;
'''

idx1 = html.find('const batShortcutCode = ')
html = html[:idx1] + deploy_ps_code + html[idx1:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Fixed index.html")
