# ⚡ 永豐 Shioaji 專業即時看盤儀表板 (AGY Edition)

專為台灣股市與期貨交易者打造的高效能本地看盤系統。基於 **FastAPI**、**WebSocket** 與 **TradingView Lightweight Charts** 開發，深度整合永豐金證券 **Shioaji** API。

支援**「高仿真即時模擬盤」**與**「正式券商實盤串流」**雙軌架構，開箱免填金鑰即可在瀏覽器體驗專業級的秒級 K 線、最佳五檔委託柱狀圖與逐筆成交流水帳。

---

## 🌟 核心功能亮點

1. **雙軌運行模式 (Zero-Config 即開即用)**：
   - 🧪 **高仿真即時模擬盤**：內建台股幾何布朗運動行情引擎，自動模擬台積電 (2330)、鴻海 (2317)、聯發科 (2454)、元大台灣50 (0050) 與台指期 (TXF) 的即時 Tick、五檔撮合與 1 分 K 線。
   - 🔴 **Shioaji 實盤連線**：填入永豐金證券 API Key 與 Secret，無縫直連券商 Solace/ZeroMQ 串流行情。
2. **極致安全 (100% Local)**：
   - 拒絕將永豐證券憑證 (`.pfx`) 與 API Key 上傳至任何雲端環境（如 Google Colab）。所有連線與計算均在本地端完成，零洩漏風險。
3. **TradingView 官方圖表引擎**：
   - 採用 Lightweight Charts 4.x，支援流暢縮放、跨時段切換、成交量副圖，以及台股習慣之「漲紅跌綠」配色。
4. **最佳五檔委託深度 (Depth-5)**：
   - 即時顯示買一~買五與賣一~賣五報價，並以雙向動態長條圖（紅色買盤、綠色賣盤）視覺化買賣單掛牌壓力。
5. **即時逐筆明細 (Tick Tape)**：
   - 毫秒級流水帳，自動判定「外盤主動買進」與「內盤主動賣出」，新成交筆數平滑動畫浮現。
6. **一鍵雙擊啟動 (Auto Launcher)**：
   - 內建 `啟動看盤儀表板.bat`，自動偵測 Python、確認依賴套件、動態避開 Port 衝突並自動開啟瀏覽器。

---

## 📂 完整檔案結構說明

```text
C:\GOOGLE ANGET\shioaji-market-dashboard\
├── server.py                   # FastAPI 後端伺服器、WebSocket 廣播與模擬行情引擎
├── 啟動看盤儀表板.bat           # 本機一鍵啟動腳本（自動偵測環境、Port切換、開瀏覽器）
├── setup_env.ps1              # PowerShell 一鍵依賴環境自動安裝腳本
├── requirements.txt           # Python 核心依賴套件清單
├── .env                       # 本機環境變數與金鑰配置檔（預設 SIMULATION 模式）
├── .env.example               # 環境變數設定範本
├── README.md                  # 給人類閱讀之專案說明與操作指南
├── SKILL.md                   # 給 AI 代理閱讀之標準技能指引文件
├── build_manual_doc.py        # 自動生成 Word 操作手冊之腳本
└── static/
    ├── index.html             # 看盤儀表板前端主網頁（響應式三欄專業終端佈局）
    ├── style.css              # 高質感深色主題樣式（彭博/TradingView風格）
    └── app.js                 # TradingView 圖表繪製、WebSocket 監聽與五檔渲染邏輯
```

---

## 🚀 跨電腦一鍵啟動與執行步驟

### 方法 1：最推薦（雙擊一鍵啟動）
直接雙擊專案目錄下的 **`啟動看盤儀表板.bat`**。
腳本將自動：
1. 偵測本機 Python 與 pip 環境。
2. 自動檢查套件完整性（FastAPI, Uvicorn, WebSockets 等）。
3. 偵測可用 Port（預設 8088，被佔用則自動順延）。
4. 自動在預設瀏覽器開啟 `http://localhost:8088`。

### 方法 2：指令手動啟動
```powershell
cd "C:\GOOGLE ANGET\shioaji-market-dashboard"
python -m uvicorn server:app --host 0.0.0.0 --port 8088
```

---

## ⚙️ 切換為永豐金證券 Shioaji 正式實盤

1. 啟動並開啟網頁看盤終端後，點擊右上角 **「⚙️ 設定」**。
2. 模式選擇 **「🔴 Shioaji 永豐正式實盤串流」**。
3. 依序填入您的 **API Key** 與 **Secret Key**。
4. 點擊 **「儲存並套用」**，系統將無縫連線至永豐金證券伺服器並訂閱即時盤況。
