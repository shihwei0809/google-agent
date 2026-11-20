# 🧪🚢 IPA (異丙醇) 報價與出貨單船期自動追蹤系統

> **專為電子化工與溶劑採購、生管與物流設計之雙單位（`台幣/公斤 TWD/KG` ⇄ `美金/公噸 USD/MT`）行情自動爬蟲、上游丙酮價差預警與出貨單「櫃號 / 船名」自動反查船公司追蹤看板**

---

## 🌟 核心功能亮點

* **💱 雙單位即時自動換算 (`台幣/公斤 TWD/KG` & `美金/公噸 USD/MT`)**：
  * 每日自動串接國際即期匯率 API (`USD/TWD`、`USD/CNY`、`CNY/TWD`)。
  * 無論供應商或行情網提供的是 `USD/MT`（東北亞 CFR 美金盤）、`RMB/MT`（華東現貨人民幣盤）或 `TWD/KG`，系統自動同步換算為 **`台幣/公斤 (TWD/KG)`** 與 **`美金/公噸 (USD/MT)`**，並自動試算 `160KG 桶裝成本` 與 `20MT ISO Tank 整槽貨值`。
* **🔍 上游原料「丙酮 (Acetone) / 丙烯 (Propylene) ➔ 異丙醇 (IPA)」加工價差預警雷達**：
  * 同時追蹤 IPA 兩大製程上游原料：**丙酮（加氫法原料）**與**丙烯（水合法原料）**。
  * 自動計算「IPA - 丙酮」每公噸美金價差與每公斤台幣價差，當上游原料連漲導致加工價差收斂低於安全水位時，自動亮燈提醒採購提前鎖單備貨。
* **🚢 出貨單「櫃號 (Container No.) / 船名 (Vessel Name)」自動反查船公司與船期追蹤**：
  * **免記船公司**：只要輸入出貨單上的 **櫃號前 4 碼**（例如 `WHLU`、`EGLV`、`YMLU`、`NRSU`、`EXFU`、`STTU`），系統 **100% 自動反查所屬船公司或 ISO Tank 化學槽罐商**，並自動判別是 **「🟣 ISO Tank 液體槽罐櫃」** 還是 **「🔵 一般危險品貨櫃 (桶裝)」**。
  * **一鍵三聯追蹤**：每筆出貨單皆提供一鍵跳轉 **🛰️ AIS 船名全球海圖即時定位 (VesselFinder)**、**⚓ 台灣港務公司靠泊預報 (TWPORT)** 及 **📦 船公司官方貨櫃動態**，並自動計算預計到港日 (ETA) 倒數天數。
* **📶 離線優先與自動重連補傳 (Offline-First & Auto-Sync)**：
  * 全面整合 `pwa_offline_sync_template.js`，斷網時新增報價或出貨單自動存入本機離線佇列，連網後秒速自動補傳。

---

## 📂 完整檔案結構說明 (File Tree - 三軌架構標準規範)

```text
IPA_報價與船期追蹤系統/
├── README.md                          # 【給人類閱讀】專案架構、功能亮點與快速啟動說明書
├── SKILL.md                           # 【給 AI 代理閱讀】環境需求、API 路由與維護指引
├── setup_env.ps1                      # 【一鍵環境安裝與部署】自動檢測 Python 套件與 Cloudflare D1 部署腳本
├── build_manual_doc.py                # 【手冊產生器】一鍵生成圖文並茂之 Word 操作手冊 (.docx)
├── IPA_報價與船期追蹤系統_操作手冊.docx # 自動產出之完整操作手冊
├── daily_auto_scraper.py              # 【定時背景爬蟲】供每日排程自動抓取匯率、重算雙單位報價並輸出 CSV 日報
├── 一鍵設定每日自動爬蟲排程.bat         # 【一鍵註冊排程】將爬蟲註冊至 Windows 工作排程器 (每日 08:00 自動執行)
│
├── 1_Web_網頁版/                      # 【軌道 1】純瀏覽器靜態網頁版 (前端直連匯率 API + LocalStorage)
│   ├── index.html
│   └── pwa_offline_sync_template.js
│
├── 2_PWA_App版/                       # 【軌道 2】PWA 獨立桌面/手機 App 版 + Python SQLite 爬蟲伺服器
│   ├── index.html                     # 含頂部智慧安裝條 (pwa-install-banner) 與新版本自動更新橫幅 (updateBanner)
│   ├── manifest.json                  # PWA Standalone 設定檔
│   ├── sw.js                          # Service Worker 離線快取與自動版本升級
│   ├── pwa_offline_sync_template.js   # 離線佇列與連網自動補傳引擎
│   ├── icons/                         # 192x192 與 512x512 高解析度 App 圖示
│   ├── run_server.py                  # Python 本機伺服器 + SQLite 歷史庫 + Port 佔用自動切換 + 區網 IP 顯示
│   └── 啟動PWA本機測試.bat             # 雙擊一鍵檢查環境、啟動伺服器並開啟瀏覽器
│
└── 3_Cloudflare_D1版/                 # 【軌道 3】Cloudflare Pages + D1 雲端無伺服器版本
    ├── public/                        # 前端靜態資源 (含完整 PWA 三件套)
    ├── functions/api/[[route]].js     # Cloudflare Pages Functions Serverless REST API
    ├── schema.sql                     # Cloudflare D1 資料表結構與初始歷史種子資料
    ├── wrangler.toml                  # Cloudflare Pages & D1 綁定設定檔
    └── 一鍵自動部署上雲端.bat           # 一鍵部署至 Cloudflare Pages
```

---

## 🚀 跨電腦一鍵啟動與執行步驟

### 方式 A：啟動本機互動看板與爬蟲伺服器（推薦）
1. 進入 `2_PWA_App版` 資料夾。
2. 雙擊執行 **`啟動PWA本機測試.bat`**。
3. 系統將自動檢測 Python 環境、建立 `data/ipa_tracker.db` SQLite 資料庫、顯示本機與區網共享網址（預設 `http://localhost:8088`，若被佔用自動切換），並自動打開瀏覽器看板。

### 方式 B：設定每天早上 08:00 自動背景爬蟲並產出 Excel (CSV) 日報
1. 在專案根目錄雙擊 **`一鍵設定每日自動爬蟲排程.bat`**。
2. 腳本會先執行一次今日即時匯率與雙單位報價抓取測試，並自動在 Windows 工作排程器註冊 `IPA_Daily_Quote_Vessel_Scraper` 任務，每天早上 08:00 自動更新資料庫並產出當日 CSV 報表。
