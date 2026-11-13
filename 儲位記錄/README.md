# 倉儲儲位 PWA 記錄系統

> 手機直接掃選儲位、批號與數量，即時無損回寫 `.xlsm` 儲位總表（自動連動分區儲位表與公式），並統計今日錄入板數與各批號入/出庫核對量。

## 核心功能亮點
- **雙倉庫支援**：完整支援 `崙尾倉儲儲位表.xlsm`（1,776 儲位）與 `鴻勝儲位表.xlsm`（860 儲位）。
- **無損回寫 Excel (`.xlsm`)**：採用 Surgical XML/ZIP 寫入引擎，精準更新總表儲存格，完整保留 VBA 巨集、圖表、資料驗證及 50+ 張分區儲位表連動公式。
- **今日板數與批號核對**：自動統計當日總錄入板數、入庫總量、出庫總量，並依「批號」彙整入庫/出庫板數與數量，方便現場對帳並一鍵匯出 CSV。
- **離線優先與自動補傳**：廠區訊號弱或斷網時，資料自動暫存本機離線佇列，連網後自動補傳回寫 Excel。
- **三軌架構**：同時提供 `1_Web_網頁版`、`2_PWA_App版`（本機區網即時寫 Excel）與 `3_Cloudflare_D1版`（雲端 Serverless API）。

## 完整檔案結構 (File Tree)

```text
儲位記錄/
├── 崙尾倉儲儲位表.xlsm              # 崙尾倉儲主檔（含 VBA 與分區公式）
├── 鴻勝儲位表.xlsm                  # 鴻勝倉庫主檔（含 VBA 與分區公式）
├── README.md                        # 本專案說明書
├── SKILL.md                         # AI 助理導航與操作指南
├── setup_env.ps1                    # 一鍵環境安裝與 Cloudflare 部署腳本
├── build_manual_doc.py              # 一鍵產出 Word / PDF 操作手冊腳本
├── 1_Web_網頁版/
│   └── index.html                   # 桌機對帳控制台網頁版
├── 2_PWA_App版/
│   ├── index.html                   # 手機優先 PWA 前端介面
│   ├── manifest.json                # PWA 安裝設定
│   ├── sw.js                        # Service Worker 離線快取與更新通知
│   ├── pwa_offline_sync.js          # 離線優先與自動重連補傳模組
│   ├── icons/                       # icon-192.png / icon-512.png
│   ├── excel_engine.py              # .xlsm 無損讀寫引擎
│   ├── run_server.py                # FastAPI 本機/區網後端伺服器
│   ├── requirements.txt             # Python 相依套件清單
│   └── 啟動PWA儲位系統.bat           # 一鍵環境檢查 + 啟動（含 Port Fallback 與區網 IP）
└── 3_Cloudflare_D1版/
    ├── public/                      # 雲端 PWA 靜態前端
    ├── functions/api/[[path]].js    # Cloudflare Pages Functions REST API
    ├── schema.sql                   # D1 SQLite 資料表定義
    ├── wrangler.toml                # Cloudflare 部署設定
    └── 一鍵自動部署上雲端.bat        # 呼叫 setup_env.ps1 部署上雲端
```

## 跨電腦一鍵啟動步驟
1. 雙擊 `2_PWA_App版\啟動PWA儲位系統.bat`（會自動檢查 Python、安裝缺少套件並啟動服務）。
2. 終端機將顯示 **手機區網網址**（例如 `http://192.168.1.50:8010`）。
3. 手機連上相同 Wi-Fi，用瀏覽器開啟該網址即可點選「立即安裝」加到手機桌面使用。
4. 寫入 Excel 前請先關閉電腦上已開啟的 `.xlsm` 檔案；每次寫入前系統會自動於 `backups/` 建立當日備份。
