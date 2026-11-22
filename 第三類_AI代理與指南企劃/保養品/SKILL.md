---
name: 保養品-manager
description: 管理與部署 AI 個人保養網站 V8（Cloudflare Pages + 共用 D1 weather-monitor-db + Workers AI/Gemini）
---

# AI 個人保養網站 V8 專案管理技能

- **正式網址**：https://skincare-ai-website.pages.dev
- **Cloudflare Pages 專案名**：`skincare-ai-website`
- **共用 D1 資料庫**：`weather-monitor-db` (`521c2592-1953-42a3-a559-bd403c8d3017`)
- **資料表前綴**：`sk_*`（已登記於 `_system_registry` 與 `C:\GOOGLE ANGET\D1_資料庫與資料表全域對照總表.md`）

## 環境與部署
1. **初始化或重灌 D1 資料**：
   `npx wrangler d1 execute weather-monitor-db --remote --yes --file="3_Cloudflare_D1版\schema.sql"`
2. **部署上線**：
   執行 `3_Cloudflare_D1版\一鍵自動部署上雲端.bat` 或 `powershell -ExecutionPolicy Bypass -File 3_Cloudflare_D1版\setup_env.ps1`。
3. **Gemini API Key（選用備援）**：
   已透過 `npx wrangler pages secret put GEMINI_API_KEY --project-name=skincare-ai-website` 加密存放於 Cloudflare 環境變數，切勿寫入程式碼。
