---
name: hs-material-quarterly-report
description: 鴻勝資材部進出貨與季年報智慧分析系統（三軌架構：Web / PWA 本機 SQLite / Cloudflare Pages + D1）
---

# AI 助理引導規範 (SKILL.md)

## 專案概述
- **專案名稱**：鴻勝資材部｜進出貨與季年報智慧分析系統
- **所在路徑**：`C:\GOOGLE ANGET\季年報資料`
- **架構模式**：標準三軌架構 (`1_Web_網頁版` / `2_PWA_App版` / `3_Cloudflare_D1版`)

## 環境依賴
- **本機 PWA 伺服器**：Python 3.10+ (`fastapi`, `uvicorn`, `openpyxl`, `python-docx`, `pillow`)
- **雲端 D1 部署**：Node.js 18+、`wrangler` CLI

## 常用執行指令
1. **一鍵初始化環境**：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup_env.ps1
   ```
2. **啟動 PWA 本機區網伺服器**（預設 Port 8092，佔用自動切換）：
   ```powershell
   .\2_PWA_App版\啟動PWA本機測試.bat
   ```
3. **部署 Cloudflare Pages + D1**：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup_env.ps1 -DeployCloudflare
   ```
4. **產生操作手冊 (.docx / .pdf)**：
   ```powershell
   python .\build_manual_doc.py
   ```

## 維護注意事項
- 修改前端邏輯 (`index.html` / `app.js` / `seed_data.js`) 時，務必同步複製到 `1_Web_網頁版`、`2_PWA_App版`、`3_Cloudflare_D1版\public` 三個目錄。
- 嚴禁將任何 `GEMINI_API_KEY` 寫入程式碼或提交至 Git；本機使用 `.env`，雲端使用 Cloudflare Pages Secret。
- Gemini Vision OCR 必須維持 `gemini-3.8-flash → 3.7 → 3.6 → 2.5 → 1.5` 降級鏈。
