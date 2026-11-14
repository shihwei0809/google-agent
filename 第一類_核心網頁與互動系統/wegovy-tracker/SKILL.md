---
name: wegovy-tracker
description: 專為 Wegovy 針劑每週施打紀錄、批號管理、動態體重折線圖、多規格筆型自訂對照與 Excel 報表匯出設計之 PWA 網頁系統，支援 Cloudflare Pages 一鍵部署與第一方持久自動存檔。
---

# Wegovy 針劑施打與體重紀錄 PWA

## 專案環境依賴
- **執行環境**：現代網頁瀏覽器 (Chrome, Edge, Safari, iOS, Android)
- **部署工具**：Cloudflare Wrangler CLI (`wrangler pages deploy`)
- **平台網域**：`https://wegovy-tracker.pages.dev`
- **資料儲存**：瀏覽器第一方持久快取 (`localStorage`，鍵名 `wegovy_multi_pens_v6`)

## AI 助理維護與行為指南
1. **沙盒隔離防呆**：若使用者將系統嵌入於 Google 協作平台 (Google Sites)，必須注意跨網域 iframe 之安全性限制；引導使用者點擊頂部提示開啟獨立網頁或加入主畫面。
2. **部署規範**：修改前端程式碼後，執行 `npx wrangler pages deploy public --project-name=wegovy-tracker --commit-dirty=true` 進行熱更新。
3. **三件套維護**：新增或修改功能時，必須同步更新 `README.md`、`SKILL.md` 及 `setup_env.ps1`。
