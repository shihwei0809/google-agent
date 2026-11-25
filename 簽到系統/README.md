# 企業活動簽到與滿意度系統 (Event Check-in & Survey System)

> 專為企業家庭日與公司活動設計的「同網址雙階段」輕量級系統：活動當天提供**數位報到 QR Code、眷屬人數勾選與活動指南**，活動結束後於後台一鍵切換為**滿意度調查專屬頁面**。支援原生 Excel (`.xlsx`) 匯入匯出、全項目後台客製化與免架設預覽。

## 核心功能亮點
- **同網址雙階段自動切換**：後台一鍵切換「🟢 活動進行中（簽到指南）」與「📝 活動已結束（滿意度調查）」，同仁認同一個網址不混亂，且後台兩套設定頁完全獨立。
- **彈性工號／姓名核對 ＋ 個資遮罩**：支援 `HS001`、`001`、`1` 或姓名查詢，前台僅顯示遮罩姓名（`王○明`）。
- **眷屬實到人數勾選 ＋ 離線報到 QR Code**：勾選實際到場眷屬與臨時新增人數，自動顯示分流組別（第 1 組／第 2 組）並產生數位憑證卡。
- **不在名單手動補簽**：補簽資料後台自動標註為 **`⚠️ 待人工核對`**。
- **原生 Excel (`.xlsx`) 雙工作表匯出與匯入**：
  - 簽到清冊 `.xlsx`（`簽到明細清冊` ＋ `各部門報到統計`）
  - 滿意度報表 `.xlsx`（`滿意度填答明細` ＋ `滿意度統計摘要`）
  - 支援 `.xlsx` 範本下載、上傳匯入、單筆新增與 Excel 複製貼上批次匯入
- **100% 後台免寫程式客製化**（預設密碼 `2027`）：
  - 公司名稱與主標題字體大小拉桿調整
  - 服務台按鈕名稱、主辦聯絡人、電話與說明備註（換部門主辦免改程式）
  - 戶外安全提醒、現場報到分流原則、費用說明、活動行程時間軸編輯器、DIY 物資核對編輯器、滿意度 4 題評分與複選項目
  - 一鍵打包下載最新獨立完整網站 (`index.html`)

## 線上正式網址 (Cloudflare Pages + D1)
- **正式站網址**：https://event-checkin-system.pages.dev
- **Cloudflare D1 資料庫**：`event-checkin-db`（ID: `586b3f3a-4682-4282-9e9c-f2a96ab14847`，APAC 區域，自動跨裝置同步設定、簽到名單與滿意度問卷）
- **後台管理預設密碼**：`2027`

## 完整檔案結構 (File Tree)
```text
簽到系統/
├── 點我預覽簽到系統(給人資看).bat       # 雙擊直接開啟瀏覽器預覽（免安裝任何環境）
├── 企業活動簽到系統_操作手冊.docx       # 最新圖文結構化操作手冊（由 build_manual_doc.py 產生）
├── README.md                           # 人類閱讀說明書
├── SKILL.md                            # AI 助理操作與維護指南
├── setup_env.ps1                       # 一鍵環境檢測與設定腳本
├── build_manual_doc.py                 # 一鍵產出最新版 Word 操作手冊腳本
├── 1_Web_網頁版/
│   └── index.html                      # 零依賴單頁互動預覽版（內建 Demo 測試名單與滿意度樣本）
├── 2_PWA_App版/
│   ├── index.html                      # 含 PWA 安裝條、自動更新條、離線補傳模組
│   ├── manifest.json                   # PWA 應用程式設定
│   ├── sw.js                           # Service Worker 離線快取
│   ├── pwa_offline_sync_template.js    # 離線佇列自動補傳模組
│   ├── icons/                          # 192x192 / 512x512 App 圖示
│   ├── run_server.py                   # Python 本機伺服器（含區網 IP 顯示與 Port 自動切換）
│   └── 啟動PWA本機測試.bat              # 本機/區網手機實測啟動檔
└── 3_Cloudflare_D1版/
    ├── public/                         # Cloudflare Pages 靜態前端（含 PWA 三件套）
    ├── functions/api/                  # Cloudflare Pages Functions (checkin.js, roster.js)
    ├── schema.sql                      # Cloudflare D1 SQLite 資料表結構
    ├── wrangler.toml                   # Cloudflare 部署設定檔
    └── 一鍵自動部署上雲端.bat           # 確認上線時之部署指引腳本
```

## 快速啟動步驟
1. **給人資預覽（免架設）**：雙擊 `點我預覽簽到系統(給人資看).bat` 或開啟 `1_Web_網頁版\index.html`，後台預設密碼為 **`2027`**。
2. **手機區網實測 (PWA)**：執行 `2_PWA_App版\啟動PWA本機測試.bat`。
3. **重新產出操作手冊**：執行 `python build_manual_doc.py`。
4. **正式上雲 (Cloudflare Pages + D1)**：依 `3_Cloudflare_D1版\一鍵自動部署上雲端.bat` 步驟部署。
