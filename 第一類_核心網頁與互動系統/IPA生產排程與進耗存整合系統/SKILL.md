---
name: IPA生產排程與進耗存整合系統
description: |
  這是一個具備 PWA 雙軌架構 (1_Web_網頁版 / 2_PWA_App版) 的 IPA 雙廠區生產排程與進耗存整合追蹤系統 v3.1。
  支援二廠試開俥運轉日設定、下腳料滿槽與原料低存量雙向警示。包含本機伺服器、圖文操作手冊自動生成 (Word / PDF) 與 clasp 推送。
---

# 🛢️ IPA 生產排程與進耗存整合系統 v3.1 (PWA 雙軌版)

## 技能與環境設定指南

本專案全面實施 Rule 8 PWA 雙軌分流架構，劃分為 `1_Web_網頁版` 與 `2_PWA_App版`。

### 依賴環境
*   **Node.js & clasp**：用於 Google Apps Script 雲端部署。
*   **Python 3.x**：執行 `run_server.py` 本機 PWA 測試伺服器與 `build_manual_doc.py` 手冊編譯。
*   **python-docx & pywin32**：生成圖文並茂之 Word (.docx) 與 PDF (.pdf) 操作手冊。
*   **Google 試算表**：ID 為 `1UdTuMJPW8QJ5XAP_ptWvPooEvnLHLaZcLEgYj8qlSPU`。

### 首次設定步驟
1. 執行 `setup_env.ps1` 自動安裝 Node.js 與 clasp。
2. 如需編譯手冊，確認 Python 安裝必要套件：`pip install python-docx pywin32`。

### 日常執行與測試指令
*   **本機 PWA 獨立 App 測試**：雙擊 `2_PWA_App版\啟動PWA本機測試.bat`。
*   **編譯圖文操作手冊 (Word + PDF)**：在 `2_PWA_App版` 執行 `python build_manual_doc.py`。
*   **推送至 Google Apps Script**：在 `1_Web_網頁版` 目錄執行 `clasp push`。
