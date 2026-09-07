# 鴻勝化學 QC 檢驗即時看板系統 (PWA 雙軌獨立版)

鴻勝化學電子級化學品進出貨樣品登錄、T100 槽車排程智慧自動帶入與品管放行即時看板系統。

## 🌟 核心特色與功能
- **🚛 T100 槽車排程智慧鎖定與自動帶入**：
  - 專門鎖定《明天進出貨排程報表(全部)20x3A00.xlsx》中「**明天進出貨排程報表(槽車)**」分頁。
  - 自動抽取：出通單號、預計時間、品名、儲位槽號、車牌/ISO Tank 櫃號、數量、客戶簡稱。
  - 提供表單上方即時下拉選單，點選後**瞬間自動填入所有 9 欄位**，現場人員只需填入姓名即可一秒完成送樣！
  - 支援前端 SheetJS 即時上傳 / 拖曳新 Excel 檔案，秒級刷新當日排程。
- **📱 PWA 雙軌架構標準 (方案一)**：
  - 支援電腦端 (Chrome/Edge) 與手機端 (Android/iOS) 一鍵安裝為獨立桌面 App。
  - 離線快取機制，即便斷網仍可流暢查看看板。
- **📊 雙欄看板與即時統計**：
  - 待驗中 vs 已檢驗完成雙欄分流、KPI 統計（待驗數、完成數、今日送樣數）。
  - 關鍵字即打即過濾、日期起訖篩選。
- **🔐 品管授權放行與 LINE 廣播通知**：
  - 放行判定需輸入 4 碼 PIN 授權碼（由試算表後台管理）。
  - 合格放行時，自動透過 LINE Messaging API 廣播放行通知。
- **🏷️ 實體標籤列印**：支援一鍵開啟格式化 2 吋送樣標籤貼紙列印。

---

## 📁 專案檔案結構 (PWA 雙軌目錄)

```text
QC-系統客製化電子化工廠/
├── 1_Web_網頁版/                    # 雲端 GAS / 網頁版
│   ├── Code.gs                     # GAS 後端 (支援 Web App 與 JSON API 雙向連線)
│   ├── Index.html                  # 具備 T100 槽車選單與 Excel 拖曳即時解析
│   ├── t100_schedule_sample.json   # 預載明天槽車 10 車次數據
│   └── README.md                   # 網頁版說明
│
├── 2_PWA_App版/                     # PWA 獨立 App 版本 (可安裝 App、離線快取、全螢幕)
│   ├── index.html                  # 整合 T100 快速選擇列 + SheetJS 即時 Excel 拖曳上傳
│   ├── manifest.json               # PWA 清單 (standalone 獨立視窗)
│   ├── sw.js                       # Service Worker 快取機制
│   ├── icons/                      # 192x192 / 512x512 高解析圖示
│   ├── run_server.py               # 本機 Python 伺服器 (自動偵測 IP 與可用 Port)
│   ├── 啟動PWA本機測試.bat          # 純 ASCII 啟動檔 (Rule 7)
│   ├── 一鍵部署到Cloudflare.bat     # Cloudflare Pages 快速部署腳本
│   ├── build_manual_doc.py         # 圖文操作手冊生成腳本 (docx)
│   └── 鴻勝化學_QC檢驗即時看板系統_操作手冊.docx # 繁體中文操作手冊
│
├── parse_excel.py                  # 後台 T100 槽車分頁專屬解析腳本
├── 明天進出貨排程報表(全部)20x3A00.xlsx # 原始排程報表範本
├── t100_tomorrow_schedule.json     # 結構化槽車排程數據
├── README.md                       # 專案主說明文件
├── SKILL.md                        # AI 助理維護指南
└── setup_env.ps1                   # 一鍵環境安裝腳本
```

---

## 🚀 快速啟動與測試

### 1. 本機 PWA 測試 (支援手機同 Wi-Fi 連線)
進入 `2_PWA_App版/` 目錄，雙擊：
👉 `啟動PWA本機測試.bat`

系統將自動尋找可用 Port，並顯示：
- 電腦本機網址：`http://localhost:8010`
- 區域網路手機網址：`http://192.168.x.x:8010`

### 2. 雲端部署至 Cloudflare Pages
在 `2_PWA_App版/` 雙擊 `一鍵部署到Cloudflare.bat`，即可一鍵上線全球 CDN。
