# 鴻勝產銷動態計畫系統 (多人線上協作版)

將原本分散於多工作表、易因複製貼上產生 `#REF!` 或跨月公式錯位之《產銷計畫 Excel》全面優化為**支援多人線上直接修改、即時多階 BOM 連動重算、甘特圖衝突偵測與雲端/本機雙軌同步**的動態網頁系統，並可隨時匯入新月份 `.xlsx` 與匯出零錯誤著色公式報表。

---

## 核心功能亮點

- **全廠製程全覆蓋 (87 品項 + 73 條 BOM)**：完整納管 **精餾** (`IPAUPS`、崙尾區 LG/日本料、`EGUPS`、勝一 S07、`CPNE4`、`ACTUPS`、`NMPUPS`、`CPNE3` 系列)、**充填** (`IPAIF`、`ACTIF`、`GAAIF`、`NMPIF-*`、`GB-014`)、**初餾** (`EBR-P1`、`CPN-P1`、`EBR95`、`DPM-1`、`DPM-B1`)、**調配** (`NSE-115`、`NSE-1106`、`NSE-1106A`、`ACT790`、`SEP73E3`、`PS300`) 及對應專屬原料。
- **修復舊版原表與舊系統五大缺陷**：
  1. 修正原 Excel `初餾產銷` `代工入庫 (+)` 被誤包入 `-SUM(H:J)` 的正負號陷阱，確保代工入庫正確正向累加。
  2. 修正原 Excel `調配產銷` `ACT790` 七月公式錯位 (`SUM(K:L)` → 本月銷售) 與 `1PG-GB` 6~7 月漏植 `SUMIF` 公式問題。
  3. 完整連動多階 BOM (`GB-014 → IPAIF/ACTIF → IPA/ACETONE`、`調配 → EGUPS → EG`、`CPNE3(T) → CPNE3 → CPNE3-R`) 與回收規則 (`IPAUPS 95% → IPA`、`2IPA → IPA`、`CPNE4(含浸) → 1CPN`)。
  4. **單月手動覆寫耗用與調整 (`✍️`)**：遇短期停車 1～2 天時，可直接點選覆寫單月總耗用或期末調整，無須破壞 BOM 公式或拆改上游排程，並可一鍵 `↺` 還原公式。
  5. **Excel 雙向無縫銜接**：瀏覽器端 SheetJS 匯入任意月份 `產銷計畫.xlsx`；ExcelJS 匯出 7 工作表、具備真公式 (`SUMIF` / `ROUND` / 結存)、凍結窗格與條件著色之報表（消除舊原型機 12,276 列冗餘日報）。
- **多人線上協作與離線優先**：Cloudflare Pages + D1 搭配樂觀鎖 (`version` 衝突比對視窗) 與歷史快照管理 (`載入/覆蓋/改名/8888密碼刪除`)；斷網時透過 `OfflineSyncManager` 自動暫存佇列並於連網後補傳。
- **產線排程甘特圖與衝突偵測**：解析多段區間 (`11~12,18~22`) 繪製 `S01/S02/S03/R01/R02/參配` 日負荷圖，自動警示同塔同日重疊及「`NMPUPS` 須避開 `IPAUPS/EGUPS`」規範。

---

## 完整檔案結構 (File Tree)

```text
鴻勝產銷動態計畫系統/
├── README.md                         # 人類使用說明書與專案檔案總覽
├── SKILL.md                          # AI 助理開發/維護指引與架構速查
├── setup_env.ps1                     # Windows 環境一鍵檢測與套件安裝腳本
├── build_manual_doc.py               # 產生 Word 操作手冊的 Python 腳本
├── 鴻勝產銷動態計畫系統_操作手冊.docx  # 自動產生的圖文操作手冊 Word 檔
├── extract_seed_from_excel.py        # 從來源 Excel 抽取初始基準 seed_data.js 之腳本
├── 1_Web_網頁版/                      # 【軌道 1】純靜態網頁版 (可雙擊 index.html 直接離線運作)
│   ├── index.html                    # 主介面 HTML
│   ├── styles.css                    # 介面樣式表
│   ├── seed_data.js                  # 基準產銷與 BOM 種子資料
│   ├── calc_engine.js                # 核心 BOM/庫存/區間計算引擎
│   ├── excel_parser.js               # SheetJS (.xlsx) 匯入解析器
│   ├── excel_exporter.js             # ExcelJS (.xlsx) 公式報表匯出器
│   ├── pwa_offline_sync.js           # PWA 離線佇列補傳模組
│   ├── app.js                        # 前端互動狀態與 UI 邏輯
│   ├── favicon.png                   # 網站圖示
│   ├── icons/                        # PWA 圖示 (192px / 512px)
│   └── vendor/                       # 離線內嵌 xlsx.full.min.js 與 exceljs.min.js
├── 2_PWA_App版/                      # 【軌道 2】本機 FastAPI + SQLite + PWA 伺服器版
│   ├── 啟動PWA本機測試.bat           # 一鍵檢查套件、顯示區網 IP、自動避開佔用 Port 並開啟瀏覽器
│   ├── requirements.txt              # Python 相依套件清單
│   ├── run_server.py                 # FastAPI + SQLite 後端與靜態伺服主程式 (預設 Port 8005+)
│   ├── schema_sqlite.sql             # 本機 SQLite 資料表建表腳本
│   └── public/                       # 與 3_Cloudflare_D1版/public 同步的前端資源與 sw.js/manifest.json
└── 3_Cloudflare_D1版/                # 【軌道 3】雲端多人即時同步正式版 (Cloudflare Pages + D1)
    ├── 一鍵自動部署上雲端.bat         # 設定系統憑證環境、推上 D1 schema 並部署 Pages
    ├── wrangler.toml                 # Cloudflare Pages 與 D1 (sales-planner-db) 綁定設定
    ├── schema.sql                    # Cloudflare D1 SQLite 資料表與 _system_registry 定義
    ├── functions/api/[[route]].js    # Pages Functions REST API (/api/health, /plan, /archives, /logs)
    └── public/                       # 雲端發布用完整靜態前端 + PWA Service Worker (sw.js)
```

---

## 跨電腦一鍵啟動與執行步驟

### 方式 A：直接開啟雲端多人同步版（推薦日常團隊協作）
- 開啟瀏覽器前往 `https://sales-planner-pwa.pages.dev`（或依公司公告網域），右上角輸入人員名稱即可線上協作修改並自動同步至 Cloudflare D1。

### 方式 B：在本機 / 區網執行 PWA 伺服器版
1. 若為全新電腦，先於專案根目錄以 PowerShell 執行 `.\setup_env.ps1`。
2. 進入 `2_PWA_App版\`，雙擊 **`啟動PWA本機測試.bat`**。
3. 視窗會顯示 `http://localhost:8005` 及區域網路同事連線 IP（若 Port 被佔用將自動順延至可用 Port）並自動開啟瀏覽器。

### 方式 C：純單機免伺服器開啟
- 直接雙擊 `1_Web_網頁版\index.html` 即可於瀏覽器內執行匯入 Excel、動態調整、甘特圖檢視與公式 Excel 匯出，資料暫存於瀏覽器本機。
