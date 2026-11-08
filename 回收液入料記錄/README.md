# 回收液入料記錄系統

這是一個專門用於記錄回收液入料過程的系統，分為「入料前」與「入料後」兩階段，確保資料準確且避免車號重複。

## 核心功能亮點
* **入料前記錄**：拍攝入料前儲槽液位與車輛照片，並輸入車號與日期。
* **狀態暫存**：入料前的資料會暫存於系統，等待入料完成。
* **入料後記錄**：入料完成後，人員可從介面選取剛才的車輛，拍攝入料後的儲槽液位。
* **Cloudflare R2 物件儲存**：照片直接由前端壓縮後上傳至 Cloudflare R2，不耗損 Google Drive 容量配額（每月 10GB 免費額度，出站流量免計費）。
* **Cloudflare D1 毫秒資料庫**：紀錄與狀態同步採用 Cloudflare D1 分散式資料庫，支援斷網離線暫存與自動背景排隊同步 (`autoSync`)。
* **防呆機制**：透過日期與車號檢查，避免重複登錄；後台刪除即時清理本地幽靈快取。

## 完整檔案結構
```text
回收液入料記錄/
├── 1_Web_網頁版/            # 一般網頁版
├── 2_PWA_App版/             # PWA 獨立 App 版 (FastAPI 後端 + SQLite)
│   ├── main.py              # FastAPI 後端程式
│   ├── static/              # 靜態檔案 (HTML/JS/CSS)
│   │   ├── index.html       # 首頁 (入料前)
│   │   ├── after.html       # 入料後介面
│   │   └── js/              # 前端邏輯
│   ├── data/                # SQLite 資料庫與照片儲存位置
│   └── requirements.txt     # Python 依賴
├── 3_Cloudflare_D1版/       # 正式生產版 (Cloudflare Pages + D1 + R2)
│   ├── functions/api/       # Cloudflare Pages Functions
│   │   ├── records.js       # D1 紀錄 CRUD API
│   │   ├── upload.js        # R2 照片上傳 API
│   │   └── photos/          # R2 照片代理串流 API ([[path]].js)
│   ├── public/              # 前端靜態資源
│   │   ├── index.html       # PWA 主頁面 (v18-D1)
│   │   ├── sw.js            # Service Worker 離線快取
│   │   └── manifest.json    # PWA 清單
│   ├── schema.sql           # D1 資料庫結構
│   └── wrangler.toml        # Cloudflare 綁定設定 (DB + PHOTOS)
├── HANDOVER.md              # 跨電腦交接日誌
├── README.md                # 專案說明書
├── SKILL.md                 # AI 代理技能說明
└── setup_env.ps1            # 環境設定腳本
```

## 線上服務網址
* **正式主站**：`https://recycle-feed-records.pages.dev`
* **備用鏡像**：`https://recycle-portal.pages.dev`
