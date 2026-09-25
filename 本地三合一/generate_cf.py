import os
import re
import shutil

cf_dir = r'c:\GOOGLE ANGET\本地三合一\3_Cloudflare_D1版'
os.makedirs(cf_dir, exist_ok=True)
os.makedirs(os.path.join(cf_dir, 'functions', 'api'), exist_ok=True)
os.makedirs(os.path.join(cf_dir, 'public'), exist_ok=True)

# 1. schema.sql (D1 資料表定義)
schema_content = '''-- D1 Database Schema for TSMC Verification System
DROP TABLE IF EXISTS verifications;
CREATE TABLE verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    material_no TEXT,
    tank_no TEXT,
    batch_no TEXT,
    supplier TEXT,
    original_location TEXT,
    target_location TEXT,
    raw_qr TEXT,
    status TEXT,
    photo_batch_url TEXT,
    photo_loc_url TEXT,
    source_order TEXT,
    doc_order TEXT
);

CREATE INDEX idx_verifications_created_at ON verifications(created_at);
CREATE INDEX idx_verifications_batch_no ON verifications(batch_no);
'''
with open(os.path.join(cf_dir, 'schema.sql'), 'w', encoding='utf-8') as f:
    f.write(schema_content)

# 2. wrangler.toml (Cloudflare Pages 設定)
wrangler_content = '''name = "tsmc-verification-system"
pages_build_output_dir = "public"
compatibility_date = "2024-03-20"

[[d1_databases]]
binding = "DB"
database_name = "tsmc-verification-db"
database_id = "YOUR_DATABASE_ID_HERE"
'''
with open(os.path.join(cf_dir, 'wrangler.toml'), 'w', encoding='utf-8') as f:
    f.write(wrangler_content)

# 3. functions/api/save.js (雙資料庫寫入 API)
save_api_content = '''export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    const body = await request.json();
    
    // 1. 寫入主資料庫 (Cloudflare D1) - 極速毫秒回應
    const stmt = env.DB.prepare(`
      INSERT INTO verifications (
        material_no, tank_no, batch_no, supplier, original_location, 
        target_location, raw_qr, status, photo_batch_url, photo_loc_url, 
        source_order, doc_order
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      body.formObject.materialNo || "", body.formObject.tankNo || "", body.formObject.batchNo || "", 
      body.formObject.supplier || "", body.formObject.deliveryPlace || "", body.targetPlace || "", 
      body.formObject.rawQr || "", body.status || "核對成功", body.photoBatchUrl || "", body.photoLocUrl || "", 
      body.sourceOrder || "", body.docOrder || ""
    );
    await stmt.run();

    // 2. 非同步雙寫入 (寫入備份資料庫 Google Sheets)
    // 使用 waitUntil 讓背景執行，不影響前台使用者的極速體驗
    const GAS_API_URL = "https://script.google.com/macros/s/AKfycbyJNqo25ny2IiwajeltMlSi1M8PnVonczlLA2UoEoxZYGSE72tiWTEJ61Y_wQhPU0H5/exec";
    
    context.waitUntil(
      fetch(GAS_API_URL, {
        method: 'POST',
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify({
          action: "processFormAndVerify", // 給 GAS 原本的邏輯處理
          formObject: body.formObject
        })
      }).catch(err => console.error("GAS Dual-Write Failed:", err))
    );

    return new Response(JSON.stringify({ 
      success: true, 
      message: "✅ 寫入 D1 成功，且已觸發 GAS 背景備份！" 
    }), { headers: { "Content-Type": "application/json" } });

  } catch (e) {
    return new Response(JSON.stringify({ success: false, message: e.toString() }), { 
      status: 500, 
      headers: { "Content-Type": "application/json" } 
    });
  }
}
'''
with open(os.path.join(cf_dir, 'functions', 'api', 'save.js'), 'w', encoding='utf-8') as f:
    f.write(save_api_content)

# 4. 複製 PWA 檔案到 public 並修改 index.html API 路徑
pwa_dir = r'c:\GOOGLE ANGET\本地三合一\2_PWA_App版'
if os.path.exists(pwa_dir):
    for item in os.listdir(pwa_dir):
        if item not in ['run_server.py', '啟動PWA本機測試.bat']:
            s = os.path.join(pwa_dir, item)
            d = os.path.join(cf_dir, 'public', item)
            if os.path.isdir(s):
                if not os.path.exists(d): shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    # 改寫 public/index.html，將 GAS 呼叫換成 Cloudflare API 呼叫
    idx_path = os.path.join(cf_dir, 'public', 'index.html')
    with open(idx_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    html = html.replace('const GAS_API_URL = "https://script.google.com/macros/s/AKfycbyJNqo25ny2IiwajeltMlSi1M8PnVonczlLA2UoEoxZYGSE72tiWTEJ61Y_wQhPU0H5/exec";', 'const GAS_API_URL = "/api/save";')
    # For GET requests, we would make a data.js API, but for now we intercept the save
    
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(html)

# 5. setup_env.ps1 (一鍵部署與自動回填)
ps1_content = '''# Cloudflare Pages + D1 自動化部署腳本
Write-Host "開始部署 Cloudflare Pages 與 D1 資料庫..." -ForegroundColor Cyan

# 1. 確認是否安裝 wrangler
if (!(Get-Command "wrangler" -ErrorAction SilentlyContinue)) {
    Write-Host "未偵測到 wrangler，正在全域安裝..." -ForegroundColor Yellow
    npm install -g wrangler
}

# 2. 登入 Cloudflare (若已登入會自動跳過)
wrangler login

# 3. 建立 D1 資料庫
Write-Host "建立 D1 資料庫 (tsmc-verification-db)..." -ForegroundColor Cyan
$d1_output = wrangler d1 create tsmc-verification-db | Out-String

# 解析 database_id
$db_id = ""
if ($d1_output -match "database_id = `"(.+?)`"") {
    $db_id = $matches[1]
    Write-Host "成功獲取 Database ID: $db_id" -ForegroundColor Green
    
    # 4. 自動回填 wrangler.toml
    $toml_path = "wrangler.toml"
    $toml_content = Get-Content $toml_path
    $toml_content = $toml_content -replace "YOUR_DATABASE_ID_HERE", $db_id
    Set-Content $toml_path $toml_content
    Write-Host "已自動更新 wrangler.toml" -ForegroundColor Green
} else {
    Write-Host "警告：無法自動獲取 database_id，請檢查 wrangler.toml 是否已手動設定。" -ForegroundColor Yellow
}

# 5. 初始化資料表結構
Write-Host "建立資料表 (schema.sql)..." -ForegroundColor Cyan
wrangler d1 execute tsmc-verification-db --file=schema.sql --remote

# 6. 部署到 Cloudflare Pages
Write-Host "部署 PWA 至 Cloudflare Pages..." -ForegroundColor Cyan
wrangler pages deploy public --project-name=tsmc-verification-system

Write-Host "✅ 部署完成！" -ForegroundColor Green
'''
with open(os.path.join(cf_dir, 'setup_env.ps1'), 'w', encoding='utf-8') as f:
    f.write(ps1_content)

print("Cloudflare + D1 Structure generated successfully!")
