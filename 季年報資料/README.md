# 鴻勝資材部｜進出貨與季年報智慧分析系統

一套專為 **鴻勝資材部** 打造的線上報表解析與差異分析系統。支援拖曳上傳 BI 下載的 **PDF 檔（文字型 & 掃描型 AI Vision OCR）** 與 **Excel 明細/彙總檔**，自動彙整為 **月報、季報、半年報、年報**，一鍵進行 **MoM / QoQ / YoY** 進貨量、出貨量、車次、倉庫棧板數差異比較，並自動產出 PPT 摘要文案、高解析統計表圖卡 (PNG) 與彙總 Excel。

## 核心功能亮點
- **BI Excel / PDF 智慧自動解析**：
  - 精準支援 `04.日報表-進貨一覽表`、`08.進貨(無小計)`、`07.月報表-月出貨明細日報表-ALL`、舊版 `.xls` 與月度/倉庫棧板橫向統計表。
  - 文字型 BI PDF 使用 `pdf.js` 零成本秒速解析；掃描圖檔 PDF 自動降級呼叫 **Gemini Flash Vision OCR**（遵循 `3.8 → 3.7 → 3.6 → 2.5 → 1.5` 降級鏈）。
- **雙軌獨立報表 & 雙 PPT 匯出（原料大車進出貨 vs 倉庫棧板作業）**：
  - **PPT① 原料大車進出貨分析**：純淨統計採購/廢液/調撥進貨與業務/調撥出貨之 **MT 與車次**（含單車載重與 BI Top 5 品名/客戶鑽取），可一鍵匯出專屬可編輯 `.pptx`、圖卡與文案。
  - **PPT② 倉庫棧板作業報表**：獨立專頁與獨立簡報，支援 **7 大作業項目**（原料進貨、客供包材進貨、自用包材進貨、成品入庫、調撥、換標或理貨作業、出貨）與 **平均每工作日作業棧板數**，一鍵產出專屬 `.pptx` 與差異說明文案。
- **預載 2022–2026 真實基準數據**：開箱即包含鴻勝資材部 2022–2025 官方季報基準、**2026 Q1 倉庫 7 項作業真實板數**、2025–2026 BI 明細彙總 + P.5 日常管理 + P.6~P.8 14 項重要工作進度。
- **4 大進階模組**：
  1. **PPT 摘要文案自動產生器**（一鍵複製直接貼入簡報）
  2. **一鍵匯出**：高解析 **PPT 統計表圖卡 (PNG)** + 多分頁 **Excel 彙總報表 (.xlsx)**
  3. **異常波動預警中心**：自訂門檻（預設 ±15%）自動標紅暴增/驟降月份
  4. **日常管理 (P.5) & 重要工作進度追蹤 (P.6~P.8)**：支援 Excel / Word (`.docx`) / PPT (`.pptx`) / PDF / 截圖 (AI OCR) / 貼上文字批次解析匯入與標準範本下載，亦支援單筆 CRUD 與離線自動同步。
- **三軌架構 + 離線優先 PWA**：支援純網頁免安裝、本機 Python SQLite 區網版、以及 Cloudflare Pages + D1 雲端多人線上版（含離線暫存自動補傳與新版本自動更新橫幅）。

## 完整檔案結構 (File Tree)
```text
季年報資料/
├── README.md                              # 專案說明書（人類閱讀）
├── SKILL.md                               # AI 助理操作規範
├── setup_env.ps1                          # 一鍵環境安裝與 Cloudflare D1 部署腳本
├── build_manual_doc.py                    # 一鍵產出操作手冊 (.docx / .pdf)
├── 1_Web_網頁版/                          # 純前端瀏覽器版（免後端，LocalStorage 儲存）
│   ├── index.html
│   ├── app.js
│   ├── seed_data.js
│   └── pwa_offline_sync.js
├── 2_PWA_App版/                           # PWA 獨立 App + Python FastAPI SQLite 本機伺服器
│   ├── index.html
│   ├── app.js
│   ├── seed_data.js
│   ├── pwa_offline_sync.js
│   ├── manifest.json
│   ├── sw.js
│   ├── icons/
│   │   ├── icon-192.png
│   │   └── icon-512.png
│   ├── run_server.py                      # 自動抓取區網 IP + Port 自動切換 + SQLite API
│   └── 啟動PWA本機測試.bat                 # 雙擊一鍵啟動（自動裝套件並開瀏覽器）
└── 3_Cloudflare_D1版/                     # Cloudflare Pages + D1 雲端多人線上版
    ├── public/                            # 雲端前端靜態檔（含完整 PWA 三件套）
    ├── functions/api/                     # Cloudflare Pages Functions REST API
    │   ├── health.js
    │   ├── metrics.js
    │   ├── management.js
    │   ├── projects.js
    │   └── ocr.js
    ├── schema.sql                         # D1 SQLite 資料表結構
    ├── wrangler.toml                      # Cloudflare 部署設定
    └── 一鍵自動部署上雲端.bat              # 一鍵建表並部署至 Cloudflare Pages
```

## 快速啟動與部署步驟
- **☁️ 雲端正式網址（Cloudflare Pages + D1，多人同步）**：https://hs-material-quarterly-report.pages.dev
1. **本機 / 區網即刻使用（推薦先測）**：雙擊 `2_PWA_App版\啟動PWA本機測試.bat`，自動偵測 Python/套件、顯示區網 IP 並開啟瀏覽器。
2. **純網頁單機開啟**：直接雙擊 `1_Web_網頁版\index.html` 即可拖曳解析 Excel/PDF 與查詢比較。
3. **部署至 Cloudflare Pages + D1 雲端線上版**：
   - 先於 `3_Cloudflare_D1版\wrangler.toml` 填入你的 `database_id`（或執行 `npx wrangler d1 create hs-material-report-db`）。
   - 雙擊 `3_Cloudflare_D1版\一鍵自動部署上雲端.bat` 即可自動套用 `schema.sql` 並部署上線。
   - 若需雲端掃描 PDF AI OCR，請在 Cloudflare Pages 後台設定環境變數 `GEMINI_API_KEY`。
