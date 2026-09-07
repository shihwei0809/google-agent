---
name: qc-系統客製化電子化工廠-manager
description: 協助使用者維護與運行「鴻勝化學 QC 檢驗即時看板系統 (PWA 雙軌版)」與 T100 槽車排程解析
---

# 鴻勝化學 QC 檢驗即時看板系統管理技能

本專案提供電子化工廠進出貨 QC 檢驗看板、T100 槽車排程智慧自動帶入與 PWA 雙軌獨立版本。

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
   執行 `2_PWA_App版/啟動PWA本機測試.bat` 或：
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
