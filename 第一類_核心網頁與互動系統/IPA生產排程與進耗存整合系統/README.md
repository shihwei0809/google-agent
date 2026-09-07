# 🛢️ IPA 生產排程與進耗存整合系統 v3.1 (PWA 雙軌標準版)

## 專案簡介
本專案為遵循開發規範之 **IPA 生產排程與進耗存整合系統 v3.1 (PWA 雙軌標準架構版)**。採用 React 18 搭配 Tailwind CSS 構建現代化動態反應式儀表板，具備 **彰濱一廠（5槽共用原料池）** 與 **彰濱二廠（TK617 LG / TK618 日本）** 雙廠區產線與儲槽進耗存精確運算、**二廠試開俥運轉日區間速設**、**下腳料滿槽上限與原料存量過低即時紅底閃爍警示**、**多月份跨月庫存遞延繼承**、**線上動態增減產線/儲槽** 與 **歷史快照雲端備份**。

> ⚠️ **區隔說明**：本系統與「IPA 崙尾產銷計畫與進耗存系統（產銷當日原料重量起算版）」為獨立分離之兩套專案，後端使用獨立 Google 試算表 ID：`1UdTuMJPW8QJ5XAP_ptWvPooEvnLHLaZcLEgYj8qlSPU`。

## 🌟 核心功能亮點 (v3.1 最新版)
*   **🏭 雙廠區架構**：
    *   **彰濱一廠**：支援 5 槽（TK604A, TK604B, TK696, TK697, TK693）共用原料池合併試算，並整合 TK652 下腳料槽。
    *   **彰濱二廠**：支援獨立儲槽（TK617 LG / TK618 日本）獨立進耗存運算，以及 TK611（支援回吃 🔄）、TK613（不可回吃 ⛔）下腳料槽。
*   **📱 PWA 雙軌獨立 App 架構 (Rule 8)**：
    *   提供 `1_Web_網頁版`（一般瀏覽器、GAS 線上部署）與 `2_PWA_App版`（獨立視窗 App、離線快取）。
    *   前端頂部內建智慧安裝導航橫幅（PWA Install Banner），支援 Chrome/Edge 一鍵安裝、Android 新增至主畫面、iOS Safari 加入主畫面指引。
    *   配齊專屬高解析度圖示（`icons/icon-192.png`、`icons/icon-512.png`）、離線快取服務（`sw.js`）與應用設定（`manifest.json`）。
*   **🚀 二廠試開俥運轉日區間速設**：支援產線獨立設定當月運轉日區間（如第 5 日至第 12 日），提供一鍵「批次套用至二廠產線」功能，非運轉日耗用自動歸零。
*   **⚠️ 智慧庫存雙向警示**：
    *   **原料槽安全庫存下限**：低於自訂下限（預設 50T）時自動顯示紅底警示 `⚠️ 原料存量過低`。
    *   **下腳料滿槽停俥風險**：高於自訂滿槽上限（預設 200T）時即時紅底閃爍 `⚠️ 滿槽停俥風險`。
*   **📦 雙模式試算引擎**：
    *   **全月產線流速滿載模式 (FLOW)**：全月份 1 日至月底依產線流速與獨立良率極限滿載試算。
    *   **產銷排產首日動態模式 (SALES)**：支援一廠共用池與二廠獨立槽位輸入產銷實體原料重量，系統自動偵測首個有排產目標之日期進行動態裁切與精準推算。
*   **📅 多月份跨月連續傳承**：自動推算連續 4 個月份，月底動態結存自動繼承為次月 1 號期初庫存。
*   **⚙️ 儲槽與產線自由設定頁 (Config Tab)**：免改程式碼即可在 UI 線上新增/刪除儲槽與產線，調控良率、流速、共用池與回吃狀態。
*   **💾 雲端備份與報表匯出**：整合 Google Sheets 資料庫即時自動儲存、自訂名稱歷史快照備份與還原，並支援一鍵匯出含 UTF-8 BOM 之 Excel (CSV) 報表。

## 📁 檔案結構 (PWA 雙軌標準架構)
```text
d:\GOOGLE ANGET\第一類_核心網頁與互動系統\IPA生產排程與進耗存整合系統\
├── 1_Web_網頁版/            # 一般瀏覽器網頁版本 (原始邏輯、GAS/Web API 後端)
│   ├── Code.gs             # 後端控制器 (試算表 ID: 1UdTuMJPW8QJ5XAP_ptWvPooEvnLHLaZcLEgYj8qlSPU)
│   ├── Index.html          # 前端 React 18 + Tailwind CSS 單頁應用程式 (v3.1)
│   └── 點我本機一鍵測試開啟.bat
└── 2_PWA_App版/             # PWA 獨立 App 版本 (可安裝 App、離線快取、全螢幕)
    ├── index.html           # 引入 manifest 與 sw.js 註冊，含頂部智慧安裝導航條
    ├── manifest.json        # PWA 配置 (名稱、standalone 獨立全螢幕、主題色)
    ├── sw.js                # Service Worker 離線快取服務
    ├── icons/               # 192x192 / 512x512 高解析 App 圖示
    ├── run_server.py        # Python 本機 Web 伺服器 (自動偵測 IP 與 Port Fallback)
    ├── 啟動PWA本機測試.bat   # 純 ASCII 啟動腳本 (呼叫 run_server.py)
    ├── build_manual_doc.py  # 圖文手冊生成腳本 (含三端 PWA 安裝指引)
    ├── IPA生產排程與進耗存整合系統_操作手冊.docx   # 繁體中文 Word 操作手冊
    └── IPA生產排程與進耗存整合系統_操作手冊.pdf    # 繁體中文 PDF 操作手冊
├── README.md               # 專案說明書
├── SKILL.md                # AI 代理技能說明與 clasp 開發規範
├── setup_env.ps1           # 一鍵安裝環境腳本
└── 點我本機一鍵測試開啟.bat
```

## 🚀 快速啟動與部署步驟
1. **本機 PWA 伺服器測試**：
   - 進入 `2_PWA_App版` 雙擊 `啟動PWA本機測試.bat`，系統會自動分配 Port 並在黑視窗中顯示本機 IP 與區域網路連線網址，同時自動開啟預設瀏覽器。
2. **部署至 Google Apps Script**：
   - 試算表 ID：`1UdTuMJPW8QJ5XAP_ptWvPooEvnLHLaZcLEgYj8qlSPU`
   - 將 `1_Web_網頁版/Code.gs` 與 `1_Web_網頁版/Index.html` 貼入 Apps Script 專案編輯器中，或使用 `clasp push` 推送。
   - 部署為「網頁應用程式 (Web App)」，執行身分設定為「我」，存取權限設定為「所有人」。
3. **重新產出圖文操作手冊**：
   - 於 `2_PWA_App版` 執行 `python build_manual_doc.py`，即可重新自動編譯更新 Word (`.docx`) 與 PDF (`.pdf`) 手冊。
