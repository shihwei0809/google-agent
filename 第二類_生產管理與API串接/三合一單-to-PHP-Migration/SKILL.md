---
name: coa-check-cloudflare-pwa-system
description: 三合一單與 COA 四重核對系統 (Cloudflare Pages + Functions + D1 + R2 + PWA) AI 助理維護指南
---

# 🤖 三合一單與 COA 四重核對系統 (Cloudflare + R2 + PWA) 技能指引

本專案將原本的三合一單核對 PHP/GAS 系統，全面升級為 **Cloudflare Pages + R2 物件儲存桶 + D1 SQLite 資料庫 + PWA 獨立應用** 之全方位無伺服器架構。

## 🛠️ 技術棧與雲端資源
1. **託管平台**：Cloudflare Pages
2. **無伺服器後端**：Cloudflare Pages Functions (`functions/api/`)
3. **雲端檔案儲存**：Cloudflare R2 Bucket (`coa-check-photos`，綁定名稱 `PHOTOS`)
4. **雲端關聯資料庫**：Cloudflare D1 (`coa-check-db`，綁定名稱 `DB`)
5. **AI 辨識**：Google Cloud Vision API (文字偵測 `TEXT_DETECTION`，支援雙 Key 奇偶秒輪詢)
6. **通訊警報**：Microsoft Teams Adaptive Card Webhook
7. **前端技術**：Tailwind CSS + Html5Qrcode + Web App Manifest + Service Worker

## 📋 三軌分流結構
- `1_Web_網頁版/`：歷史 PHP / MySQL 實作保存。
- `2_PWA_App版/`：本機可安裝 PWA 測試版本 (Python 伺服器啟動)。
- `3_Cloudflare_R2_D1版/`：雲端正式版本（包含 public 前端、functions 後端、wrangler.toml 與部署腳本）。

## ⚙️ 常用指令
- 部署至 Cloudflare Pages：`cd 3_Cloudflare_R2_D1版 && npx wrangler pages deploy public --project-name=coa-check-pwa`
- 執行本機模擬 (含 D1 與 R2 模擬)：`cd 3_Cloudflare_R2_D1版 && npx wrangler pages dev public --d1=DB=coa-check-db --r2=PHOTOS=coa-check-photos --port=8788`
- 初始化 D1 結構：`cd 3_Cloudflare_R2_D1版 && npx wrangler d1 execute coa-check-db --file=./schema.sql --remote`
