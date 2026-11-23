---
name: 鴻勝產銷動態計畫系統
description: 精餾/充填/初餾/調配產銷與多階 BOM 進耗存動態排程網頁系統之開發、同步與維護指南。
---

# AI 助理開發與維護規範 (SKILL.md)

## 1. 專案概覽與三軌架構
- **系統名稱**：鴻勝產銷動態計畫系統 (`sales-planner-pwa`)
- **線上位置**：`https://sales-planner-pwa.pages.dev`
- **Cloudflare D1**：`sales-planner-db` (`24ff2b96-529d-4337-bc00-8ef99ea41551`，資料表前綴 `sp_`)
- **三軌同步守則**：修改前端程式 (`index.html`, `styles.css`, `calc_engine.js`, `excel_parser.js`, `excel_exporter.js`, `app.js`, `seed_data.js`, `sw.js`, `manifest.json`) 時，必須先於 `2_PWA_App版/public/` 測試驗證，並同步複製至 `3_Cloudflare_D1版/public/` 與 `1_Web_網頁版/`。

## 2. 相依環境與常用指令
- **Python 環境**（供 `2_PWA_App版/run_server.py` 與手冊/種子腳本使用）：
  - `fastapi`, `uvicorn`, `openpyxl`, `python-docx`
  - 初始化：`powershell -ExecutionPolicy Bypass -File .\setup_env.ps1`
  - 啟動本機測試：`.\2_PWA_App版\啟動PWA本機測試.bat`
- **Node.js / Wrangler 驗證與雲端部署**：
  - 語法檢查：`node --check 2_PWA_App版/public/*.js`
  - 單元對帳測試（比對 `source_plan.xlsx` 計算與 ExcelJS 公式匯出）
  - 企業代理下執行 `wrangler` 前**務必**設定 `$env:NODE_OPTIONS = "--use-system-ca"`
  - 更新 D1 Schema：`npx wrangler d1 execute sales-planner-db --remote --file=3_Cloudflare_D1版/schema.sql`

## 3. 核心技術細節
- **純 JS 計算引擎 (`calc_engine.js`)**：同時支援瀏覽器 `window.SalesPlannerEngine` 與 Node `require()`。內含 6 輪收斂迴圈處理多階 BOM (`GB-014 -> IPAIF/ACTIF`、`調配 -> EGUPS`、`CPNE3(T) -> CPNE3 -> CPNE3-R`) 與回收規則。
- **單月手動覆寫 (`usageOverride`)**：允許對任何原料或半成品於特定月份覆寫 `有效總耗用`，並可一鍵還原 `null`。
- **樂觀鎖併發控制 (`/api/plan`)**：前端攜帶 `version`，若後端已有較新版則回傳 HTTP `409 Conflict` 觸發衝突解決視窗。
- **非同步離線補傳 (`pwa_offline_sync.js`)**：使用 `OfflineSyncManager`，離線佇列儲存於 `sp_offline_queue_v1`。
