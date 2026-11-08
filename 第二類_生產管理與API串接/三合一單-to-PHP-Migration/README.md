# 📦 三合一單與 COA 四重核對系統 (Cloudflare Pages + R2 + D1 + PWA)

本專案為廠區原料進料與地磅三合一單、COA 檢驗報告自動化比對系統。支援從紙本/電子單據快速透過 QR Code 掃描或 Google Vision AI 視覺光學辨識，自動讀取「料號、槽號、批號、送達地點、供應商」，並對現場所拍攝之「COA 批號照片」與「地磅/系統照片」進行嚴密的四重邏輯驗證與 T100 廠區組合比對，最後將相片永久封存於 **Cloudflare R2 物件儲存桶**，比對數據與審核日誌即時寫入 **Cloudflare D1 分散式資料庫**，並自動推播 **Microsoft Teams** 警報工作流程。

---

## 🌟 核心功能亮點

1. **三軌架構全面分流 (Three-Track Architecture)**：
   - 🌐 **1_Web_網頁版**：保留原始 PHP + MySQL 經典後端版本。
   - 📱 **2_PWA_App版**：本機可安裝獨立 App 版本，配備智慧自動 Port 切換與區網 IP 顯示之 Python 伺服器。
   - ☁️ **3_Cloudflare_R2_D1版**：Serverless 雲端架構（Cloudflare Pages + Functions + D1 + R2 + PWA），全球邊緣節點極速響應、零伺服器維護成本。
2. **📸 雙重智慧輸入模式**：
   - **QR Code 掃描**：極速解碼 `||料號||槽號||批號||供應商||送達地點` 規格。
   - **AI 讀單 (Google Vision OCR)**：單擊紅鈕拍攝三合一單，智慧辨識各項欄位並自動填入。
3. **🛡️ 嚴格四重交叉核對機制**：
   - **關卡 1 (COA 批號)**：核對 COA 照片中之批號，支援去開頭前綴與光學字元模糊映射 (如 O/0, I/1, S/5)。
   - **關卡 2 (地磅地點 - V45 升級)**：支援標準包含比對與 T100 拆解組合比對（提取照片中「廠別 4 碼」+「廠區 3 碼」組合比對去頭尾地點代碼）。
   - **關卡 3 (地磅槽號)**：自動遮蔽批號字串以防子字串誤命中，比對獨立槽號標記。
   - **關卡 4 (地磅系統批號)**：深度核對地磅單據上的系統批號，核對失敗時列出候選字供快速除錯。
4. **☁️ Cloudflare R2 + D1 + Google 試算表 (雙邊寫入機制 Dual Write)**：
   - **R2 照片儲存桶**：照片經由前端防崩潰壓縮 (800px / JPEG 0.6) 後，由 Worker 安全寫入 R2 (`/api/photos/...`)，具備 ETag 304 與全域快取。
   - **D1 SQLite 資料庫**：毫秒級紀錄每次核對時間、料號、雙單號（來源單號 `ESXM101-`、磅單號 `ESXM201-`）、成功/失敗詳細原因。
   - **Google 試算表即時雙向同步**：核對完成後自動非同步推送到 Google Sheets（依月份分頁 `YYYYMM` 與 `Error_Log` 歸檔），主管與現場人員可直接在 Google 試算表整理、篩選、畫圖表！
   - **動態向 GAS 要金鑰**：金鑰統一在 Google 試算表「設定」分頁維護，Cloudflare 啟動時自動動態向 GAS 抓取，免改程式碼！
5. **📲 完整 PWA 獨立應用支援**：
   - 支援手機/桌面安裝至主畫面（`display: standalone`）。
   - 頂部智慧安裝條提示，Service Worker 快取靜態資源，斷網仍可開啟 App。
6. **🚨 Microsoft Teams 即時警報**：
   - 失敗時自動觸發 Teams Adaptive Card Webhook，即時通知現場工程師與管理人員。

---

## 📂 完整目錄結構 (File Tree)

```text
三合一單-to-PHP-Migration/
├── 1_Web_網頁版/                    # 原始 PHP + MySQL 經典版本
│   ├── index.html                   # 前端相機與表單介面
│   ├── process.php                  # 核心四重比對 PHP 後端 (V45)
│   ├── process_ai_read.php          # Google Vision AI 讀單 PHP
│   ├── query.php                    # MySQL 歷史紀錄查詢頁
│   └── CODE.txt                     # 原始 Google Apps Script (GAS) 歷史備份代碼
│
├── 2_PWA_App版/                     # 本機/離線可安裝 PWA 獨立 App 版本
│   ├── icons/                       # 192x192, 512x512 高解析 App 圖示
│   ├── index.html                   # PWA 主頁面 (含智慧安裝條與 Service Worker 註冊)
│   ├── query.html                   # 紀錄查詢與照片預覽頁
│   ├── manifest.json                # Web App Manifest 配置
│   ├── sw.js                        # Service Worker 離線快取核心
│   ├── run_server.py                # Python 本機 Web 伺服器 (自動 Port Fallback + 顯示本機 IP)
│   └── 啟動PWA本機測試.bat           # 一鍵啟動本機 PWA 測試
│
├── 3_Cloudflare_R2_D1版/            # Cloudflare Pages + Functions + D1 + R2 雲端版本
│   ├── public/                      # 前端靜態資源
│   │   ├── icons/                   # PWA 應用圖示
│   │   ├── index.html               # PWA 四重核對操作介面
│   │   ├── query.html               # 雲端紀錄列表 (含 R2 照片燈箱預覽與 CSV 匯出)
│   │   ├── manifest.json            # PWA 描述檔
│   │   └── sw.js                    # 離線快取腳本
│   ├── functions/                   # Cloudflare Pages Functions (Serverless API)
│   │   └── api/
│   │       ├── ai-read.js           # Google Vision AI 讀單 API
│   │       ├── verify.js            # 四重核對 + R2 照片寫入 + D1 紀錄 + Teams 推播
│   │       ├── query.js             # D1 分頁搜尋與紀錄查詢 API
│   │       ├── config.js            # 系統設定動態管理 API
│   │       └── photos/
│   │           └── [[path]].js      # R2 照片極速代理串流 (CDN 邊緣快取 1 年)
│   ├── Code.gs                      # Google Apps Script 雙向同步程式 (向試算表要金鑰 + 寫入資料)
│   ├── schema.sql                   # Cloudflare D1 資料表定義 (主表, 設定, 日誌)
│   ├── wrangler.toml                # Cloudflare Pages, D1, R2 綁定設定
│   ├── init_d1_r2.bat               # 一鍵初始化 D1 與 R2 儲存桶
│   ├── 本地預覽除錯.bat             # 使用 wrangler pages dev 模擬雲端運行
│   └── 一鍵自動部署上雲端.bat        # 自動套用 schema 並發布至 Cloudflare Pages
│
├── 一鍵啟動_Cloudflare本地測試.bat   # 根目錄快捷指令：啟動 Cloudflare 模擬環境
├── 一鍵啟動_PWA本機測試.bat          # 根目錄快捷指令：啟動 Python PWA 伺服器
├── setup_env.ps1                    # 環境自動檢查與初始化腳本
├── SKILL.md                         # 給 AI 助理閱讀的維護指引
└── README.md                        # 給人類閱讀的高質感專案說明書
```

---

## 🚀 跨電腦一鍵啟動與部署步驟

### 模式 A：Cloudflare 雲端部署 (正式環境)
1. 進入 `3_Cloudflare_R2_D1版` 資料夾。
2. 首次建置請雙擊 **`init_d1_r2.bat`** 建立 R2 儲存桶 (`coa-check-photos`) 與 D1 資料庫 (`coa-check-db`)。
3. 雙擊 **`一鍵自動部署上雲端.bat`**，自動將靜態頁面與 Serverless Functions 發布上線。

### 模式 B：Cloudflare 本機模擬除錯 (免上傳即可測試 API + R2 + D1)
- 雙擊根目錄 **`一鍵啟動_Cloudflare本地測試.bat`**，系統將以 `wrangler pages dev` 模擬 D1 與 R2 儲存桶，瀏覽網址為 `http://localhost:8788`。

### 模式 C：PWA 離線測試伺服器 (單機或區域網路測試)
- 雙擊根目錄 **`一鍵啟動_PWA本機測試.bat`**，系統會自動切換可用 Port 並在終端機顯示局域網 IP，手機連接同一 Wi-Fi 即可安裝使用。
