# AI 個人保養網站 V8（Cloudflare Pages + 共用 D1 + Workers AI / Gemini）

## 專案簡介
將原 Google Apps Script + Google Sheets 保養品管理系統全面升級至 **Cloudflare Pages + D1 Serverless 架構**，支援 PWA 安裝、離線佇列補傳、雙引擎 AI 諮詢（Cloudflare Workers AI + Google Gemini Flash 多階降級），並併入既有共用資料庫 `weather-monitor-db`（所有資料表加上 `sk_` 前綴 100% 防撞隔離）。

## 線上正式網址
- **Cloudflare Pages**：https://skincare-ai-website.pages.dev
- **預設測試帳號**：`shihwei` / PIN：`1234`
- **共用 D1 資料庫**：`weather-monitor-db` (`521c2592-1953-42a3-a559-bd403c8d3017`)
- **全域資料庫防忘總表**：[D1_資料庫與資料表全域對照總表.md](file:///C:/GOOGLE%20ANGET/D1_資料庫與資料表全域對照總表.md)

## 核心功能
- 完整遷移原試算表 22 項產品、17 筆使用指南、膚況總覽、早晚流程、防曬排行、避雷與平替清單。
- 每日勾選清單雲端 D1 同步，支援斷網離線暫存與連網自動補傳。
- 雙引擎 AI 保養顧問：免費 Cloudflare Workers AI（`@cf/meta/llama-3.3-70b-instruct-fp8-fast` 等多階降級）× Google Gemini Flash（`3.8` → `2.5` 多階降級），支援 AI 自動評估並寫入新產品。
- 內建 `🗄️ D1 防忘總表` 分頁，直接從 D1 `_system_registry` 即時檢視共用資料庫內各系統資料表歸屬。

## 檔案結構
```text
保養品/
├── Code.gs                     # 舊版 GAS 後端（保留備份）
├── Index.html                  # 舊版前端（保留備份）
├── README.md                   # 本說明書
├── SKILL.md                    # AI 助理操作指引
└── 3_Cloudflare_D1版/
    ├── wrangler.toml           # Cloudflare Pages + D1 + Workers AI 綁定設定
    ├── schema.sql              # D1 建表、_system_registry 登記與完整種子資料
    ├── functions/
    │   └── api/
    │       └── skincare.js     # Cloudflare Pages Functions REST API
    ├── public/
    │   ├── index.html          # V8 PWA 前端介面
    │   ├── manifest.json       # PWA 清單
    │   ├── sw.js               # Service Worker（自動更新 + 離線快取）
    │   └── icons/              # 192x192 & 512x512 App 圖示
    ├── setup_env.ps1           # PowerShell 自動部署腳本
    └── 一鍵自動部署上雲端.bat   # 一鍵部署啟動檔
```

## 一鍵部署
雙擊 `3_Cloudflare_D1版\一鍵自動部署上雲端.bat`，或執行：
```powershell
cd "C:\GOOGLE ANGET\第三類_AI代理與指南企劃\保養品\3_Cloudflare_D1版"
npx wrangler pages deploy public --project-name=skincare-ai-website --branch=main
```
