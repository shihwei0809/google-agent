---
name: qc-系統客製化電子化工廠-manager
description: 協助使用者維護與運行「鴻勝化學 QC 檢驗即時看板系統 (PWA 雙軌版)」、T100 槽車排程解析與 Microsoft Teams 分流通報
---

# 鴻勝化學 QC 檢驗即時看板系統管理技能

本專案提供電子化工廠進出貨 QC 檢驗看板、T100 槽車排程智慧自動帶入、Microsoft Teams 精準分流通知、2 小時超時預警與 PWA 雙軌獨立版本。

## 🛠️ 環境依賴需求
1. **Python 3.x**：執行 `run_server.py` 本機伺服器、`parse_excel.py` 解析腳本及 `build_manual_doc.py`。
   - 必備套件：`openpyxl`, `python-docx`, `pillow`
2. **Node.js (選擇性)**：若需使用 Wrangler 部署至 Cloudflare Pages。

## 🚀 常用執行指令
1. **環境檢查與安裝**：
   ```powershell
   powershell -ExecutionPolicy Bypass -File setup_env.ps1
   ```
2. **啟動本機 PWA 伺服器**：
   雙擊 `點我啟動PWA本機測試.bat` 或：
   ```powershell
   python 2_PWA_App版/run_server.py
   ```
3. **解析最新 T100 槽車 Excel 排程**：
   ```powershell
   python parse_excel.py
   ```
4. **生成最新 Word 操作手冊**：
   ```powershell
   python 2_PWA_App版/build_manual_doc.py
   ```
5. **Teams 頻道 Webhook 設定引導**：
   - 雲端設定：於 Google 試算表 `System_Config` 分頁維護 `TEAMS_MANAGER_WEBHOOK` 與各課室 Webhook。
   - 本機測試：直接於 PWA 網頁端點選「⚙️ Teams Webhook 設定與卡片測試」，即可進行免聯網互動卡片預覽或真實推送。
