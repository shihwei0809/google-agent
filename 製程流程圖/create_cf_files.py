import os

def write_file(path, content):
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

# 1. manifest.json
write_file('public/manifest.json', '''
{
  "name": "ChemFlow Pro",
  "short_name": "ChemFlow",
  "start_url": "/index.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#4f46e5",
  "icons": [
    {
      "src": "icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
''')

# 2. sw.js
write_file('public/sw.js', '''
const CACHE_NAME = 'chemflow-pro-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
''')

# 3. schema.sql
write_file('schema.sql', '''
CREATE TABLE IF NOT EXISTS flow_data (
    id TEXT PRIMARY KEY,
    json_data TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

# 4. wrangler.toml
write_file('wrangler.toml', '''
name = "chemflow-pro"
pages_build_output_dir = "public"
compatibility_date = "2024-01-01"

[[d1_databases]]
binding = "DB"
database_name = "chemflow_pro_db"
database_id = "" # Will be filled by setup_env.ps1
''')

# 5. save.js
write_file('functions/api/save.js', '''
export async function onRequestPost(context) {
  const req = await context.request.json();
  const db = context.env.DB;
  const jsonData = JSON.stringify(req);
  await db.prepare('INSERT OR REPLACE INTO flow_data (id, json_data) VALUES (?, ?)').bind('default_save', jsonData).run();
  return new Response(JSON.stringify({success: true}), {headers: {'Content-Type': 'application/json'}});
}
''')

# 6. load.js
write_file('functions/api/load.js', '''
export async function onRequestGet(context) {
  const db = context.env.DB;
  const result = await db.prepare('SELECT json_data FROM flow_data WHERE id = ?').bind('default_save').first();
  if (result) {
    return new Response(result.json_data, {headers: {'Content-Type': 'application/json'}});
  }
  return new Response(JSON.stringify({nodes: [], wires: []}), {headers: {'Content-Type': 'application/json'}});
}
''')

# 7. ai_chat.js (Multi-key fallback implementation)
write_file('functions/api/ai_chat.js', '''
export async function onRequestPost(context) {
  const { message } = await context.request.json();
  const env = context.env;
  
  // Rule 7: Multi-key support & Fallback
  const keys = (env.GEMINI_KEYS || "").split(",").filter(k => k);
  if (keys.length === 0) return new Response(JSON.stringify({reply: "未設定 API Key"}), {status: 200});

  let reply = "所有金鑰皆已超限或失效";
  
  for (let key of keys) {
    try {
      const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key=${key}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contents: [{ parts: [{ text: `你是一位化工廠製程專家，請用繁體中文回答：${message}` }] }] })
      });
      
      if (resp.ok) {
        const data = await resp.json();
        reply = data.candidates[0].content.parts[0].text;
        break; // Success, break fallback loop
      }
    } catch (e) {
      console.error(e);
      // Fallback to next key
    }
  }
  
  return new Response(JSON.stringify({ reply }), {headers: {'Content-Type': 'application/json'}});
}
''')

# 8. ai_image.js
write_file('functions/api/ai_image.js', '''
export async function onRequestPost(context) {
  const { prompt } = await context.request.json();
  const env = context.env;
  const keys = (env.OPENAI_KEYS || "").split(",").filter(k => k);
  if (keys.length === 0) return new Response(JSON.stringify({error: "未設定 API Key"}), {status: 200});

  let imageUrl = null;
  
  for (let key of keys) {
    try {
      const resp = await fetch("https://api.openai.com/v1/images/generations", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${key}`
        },
        body: JSON.stringify({
          model: "dall-e-3",
          prompt: `一個工業製程圖/設備：${prompt}。專業、清晰、工業風。`,
          n: 1,
          size: "1024x1024"
        })
      });
      
      if (resp.ok) {
        const data = await resp.json();
        imageUrl = data.data[0].url;
        break;
      }
    } catch (e) {
      // Fallback
    }
  }
  
  return new Response(JSON.stringify({ imageUrl }), {headers: {'Content-Type': 'application/json'}});
}
''')

# 9. README.md
write_file('README.md', '''
# ChemFlow Pro 雲端版

*   **核心功能**：工業製程動態流向編輯、Cloudflare D1 雲端存檔、AI 助手問答、AI 設備建圖生成。
*   **檔案結構**：
    *   `public/`: PWA 與前端靜態檔案 (包含主程式 index.html)。
    *   `functions/api/`: Cloudflare Pages Functions 後端 (儲存與 AI)。
    *   `schema.sql`: D1 資料庫結構。
*   **部署方式**：執行 `setup_env.ps1` 進行一鍵安裝與 Cloudflare 部署。
''')

# 10. SKILL.md
write_file('SKILL.md', '''
---
name: ChemFlow Pro 雲端版
description: 整合 AI 與 D1 資料庫的 PWA 製程圖工具
---
# 安裝與啟動指引
1. 確保已安裝 Node.js 與 PowerShell。
2. 執行 `./setup_env.ps1` 自動建立 D1 資料庫、配置 Wrangler，並部署至 Cloudflare Pages。
''')

# 11. setup_env.ps1
write_file('setup_env.ps1', '''
Write-Host "正在安裝與部署 ChemFlow Pro 雲端版..."
npm install -g wrangler

Write-Host "登入 Cloudflare..."
wrangler login

Write-Host "建立 D1 資料庫..."
$dbOutput = wrangler d1 create chemflow_pro_db
$dbId = ($dbOutput | Select-String -Pattern "database_id = `"(.+?)`"").Matches.Groups[1].Value

if ($dbId) {
    Write-Host "取得 Database ID: $dbId"
    (Get-Content wrangler.toml) -replace 'database_id = ""', "database_id = `"$dbId`"" | Set-Content wrangler.toml
}

Write-Host "初始化資料表..."
wrangler d1 execute chemflow_pro_db --file=schema.sql --remote

Write-Host "部署至 Cloudflare Pages..."
wrangler pages deploy public --project-name chemflow-pro

Write-Host "部署完成！請至 Cloudflare Dashboard 設定環境變數 GEMINI_KEYS 與 OPENAI_KEYS。"
''')

# 12. build_manual_doc.py
write_file('build_manual_doc.py', '''
print("產出操作手冊.docx 與 .pdf ... (此為佔位腳本，實際可使用 python-docx 與 pdfkit)")
with open("ChemFlow_Pro_操作手冊.txt", "w", encoding="utf-8") as f:
    f.write("ChemFlow Pro 操作手冊\\n1. 網頁版與 PWA 安裝指引\\n2. AI 助手操作\\n3. 雲端存檔。")
''')

print("Created all files successfully.")
