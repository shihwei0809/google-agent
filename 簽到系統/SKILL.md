---
name: event-checkin-system
description: 企業活動簽到與滿意度系統（同網址雙階段切換、工號/姓名遮罩核對、眷屬勾選、報到 QR Code、原生 Excel .xlsx 匯入匯出、全項目後台客製化）
---

# 企業活動簽到與滿意度系統 SKILL

## 1. 專案資訊
- **目錄**：`C:\GOOGLE ANGET\簽到系統`
- **線上正式網址**：https://event-checkin-system.pages.dev
- **Cloudflare D1 資料庫**：`event-checkin-db`（`586b3f3a-4682-4282-9e9c-f2a96ab14847`，binding: `DB`）
- **後台預設密碼**：`2027`
- **架構**：三軌架構（`1_Web_網頁版` / `2_PWA_App版` / `3_Cloudflare_D1版`）

## 2. 環境依賴
- 預覽版：無需安裝依賴（SheetJS CDN 產生 `.xlsx`，離線時自動降級為 `.xls` XML）。
- PWA 本機伺服器：Python 3.9+（標準函式庫）。
- 操作手冊產生 (`build_manual_doc.py`)：`python-docx`（可執行 `setup_env.ps1` 安裝）。
- 正式上雲：Node.js + `wrangler` CLI（Cloudflare Pages + D1）。

## 3. 常用指令
- **開啟預覽版**：雙擊 `點我預覽簽到系統(給人資看).bat`
- **啟動 PWA 本機測試**：`2_PWA_App版\啟動PWA本機測試.bat`
- **更新 Word 操作手冊**：`python build_manual_doc.py`
- **環境初始化**：`powershell -ExecutionPolicy Bypass -File setup_env.ps1`

## 4. AI 維護須知
- 修改 `1_Web_網頁版\index.html` 後，務必同步更新 `2_PWA_App版\index.html` 與 `3_Cloudflare_D1版\public\index.html`。
- 新增或變更功能後，需同步更新 `build_manual_doc.py`、`README.md` 並重新執行 `python build_manual_doc.py` 產出最新 `.docx`。
