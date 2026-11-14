# 💉 Wegovy 針劑施打與體重紀錄系統 (Wegovy Tracker PWA)

專為每週定期施打 Wegovy 減重針劑設計之動態管理與體重趨勢分析系統。解決 Google 協作平台 (Google Sites) 動態隨機沙盒 iframe 導致 `localStorage` 遺失的問題，部署於 Cloudflare Pages 獨立第一方網域，提供真正的本機與離線持久自動存檔。

---

## 🌟 核心功能亮點
- ☁️ **跨設備雲端即時同步 (Cloudflare KV + Functions)**：免帳號密碼，輸入同一組自訂或隨機 6 碼同步代碼，即可在 iPhone 瀏覽器、主畫面 App、電腦、iPad 之間即時雙向連線同步，換設備或加入主畫面不掉資料。
- 📊 **Chart.js 動態體重記錄曲線圖**：圓滑漸層折線圖，自動縮放 Y 軸刻度，支援懸浮提示施打劑量與體重數值。
- 📗 **一鍵匯出專業 Excel 報表 (.xlsx)**：支援將全期跨筆與各週施打明細、劑量、體重、週變化及累計減重一鍵匯出為格式化試算表，方便看診與存檔。
- 👁️ **雙視角自由切換**：可一鍵切換「當前筆紀錄」或「全期跨筆累計總覽」。
- 🎯 **四大核心指標看板**：起始體重、最新體重、累計減重（自動計算）、自訂目標體重與剩餘目標差距。
- 📅 **視覺化日曆選擇器**：全面換裝原生日期選擇器，附「設為今天」與「⚡ 依首週自動推算每週(+7天)」功能。
- 🏷️ **多支筆分頁與批號統一設定**：每支筆統一設定看診日/開始日與藥品批號，週次與劑量精準對照。
- ⚙️ **筆型規格切換與自訂格數對照**：支援 1.0mg、1.7mg、2.4mg 官方常見規格一鍵切換，亦可自訂編輯各檔位之格數與劑量文字，表格下拉選單自動同步連動。
- 💾 **即時自動存檔指示燈**：每次編輯皆有毫秒級儲存狀態提示，重整、重開、離線存檔永久穩固。
- 📥 **完整的備份匯入與匯出**：提供標準 JSON 備份檔匯出與一鍵匯入功能。
- 📱 **PWA 支援**：支援手機與平板點擊「加入主畫面」，化身為獨立原生 App。

---

## 📂 完整檔案結構說明 (File Tree)
```text
D:\GOOGLE ANGET\第一類_核心網頁與互動系統\wegovy-tracker\
├── functions\
│   └── api\
│       └── sync.js              # Cloudflare Pages Functions (雲端同步 KV Serverless API)
├── public\
│   ├── index.html               # 核心前端主頁面 (HTML5 / Tailwind CSS / Chart.js / 本機快取 / 雲端同步)
│   └── manifest.json            # PWA 應用程式清單設定檔
├── wrangler.toml                # Cloudflare Pages 與 KV Namespace (WEGOVY_SYNC) 設定
├── 一鍵部署至Cloudflare.bat      # 一鍵部署至 Cloudflare Pages (wegovy-tracker)
├── README.md                    # 給人類閱讀之專案完整說明書
├── SKILL.md                     # 給 AI 助理閱讀之技術規範與行為說明書
└── setup_env.ps1                # 一鍵安裝環境相依腳本 (Wrangler / Node 環境檢查)
```

---

## 🚀 線上網址與部署方式
- ☁️ **Cloudflare Pages 線上正式站點**：https://wegovy-tracker.pages.dev
- ⚡ **本機一鍵部署**：直接雙擊執行 `一鍵部署至Cloudflare.bat`，即可自動發布至 Cloudflare Pages。
