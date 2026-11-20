---
name: ipa-quote-and-vessel-tracker
description: IPA (異丙醇) 與上游原料 (丙酮/丙烯) 每日報價雙單位 (TWD/KG & USD/MT) 自動換算、加工價差預警及出貨單櫃號/船名自動反查船公司追蹤系統。
---

# 🤖 AI 代理維護與操作指引 (SKILL.md)

## 1. 專案定位與核心商業邏輯
本系統專為解決化工原物料採購與物流追蹤的兩大痛點而設計：
1. **不知道哪家船公司也能查船期**：透過出貨單上的 **櫃號前 4 碼 (BIC / SCAC Code)** 自動反查船公司（如 `WHLU`=萬海、`EGLV`=長榮、`YMLU`=陽明）或 ISO Tank 專業槽罐營運商（如 `NRSU`=日陸物流、`EXFU`=EXSIF、`STTU`=Stolt），並結合 **船名 (Vessel Name)** 自動生成 AIS 海圖船位、台灣港務公司靠泊預報與船公司查櫃連結。
2. **雙單位即時換算 (`台幣/公斤 TWD/KG` & `美金/公噸 USD/MT`)**：每日自動抓取即期匯率 (`open.er-api.com`)，將任意來源幣別（`USD/MT`、`RMB/MT`、`TWD/KG`）統一換算為 `TWD/KG` 與 `USD/MT`，並計算「丙酮 ➔ IPA 加工價差 (Crack Spread)」預警。

## 2. 環境需求與一鍵初始化
* **作業系統**：Windows 10 / 11
* **Python 版本**：Python 3.9+
* **必要套件**：`requests`, `pillow`, `python-docx`
* **初始化指令**：
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\setup_env.ps1
  ```

## 3. 常用執行指令
* **啟動本機 PWA 與 SQLite 爬蟲伺服器**：
  ```powershell
  python .\2_PWA_App版\run_server.py 8088
  ```
* **執行單次每日定時爬蟲並產出 CSV 日報**：
  ```powershell
  python .\daily_auto_scraper.py
  ```
* **重新產出 Word 操作手冊**：
  ```powershell
  python .\build_manual_doc.py
  ```
