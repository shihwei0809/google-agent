# Agilent GC/LC 氣相/液相層析數據視覺化與轉檔系統 (`agilent-gc-lc-viewer`)

本系統專為公司同仁於**跨電腦免安裝 Agilent 原廠昂貴軟體（ChemStation / OpenLab）**時使用。只需雙擊 `.bat` 啟動檔，即可透過極簡網頁介面拖曳讀取 Agilent `.ch` 或 `.D` 資料夾（ZIP 打包檔），即時繪製滯留時間（Retention Time）與訊號強度（Abundance）層析圖譜，並自動估算 Peak 峰面積與匯出 CSV / Multi-sheet Excel 報表。

---

## 🌟 核心功能亮點

- ⚡ **免授權免安裝原廠軟體**：內建純 Python 二進位解析引擎，可直接讀取 `.ch` 訊號檔。
- 📊 **現代化互動層析圖**：支援放大/縮小、游標標記滯留時間與訊號強度。
- 🔍 **自動尋峰與積分**：自動偵測 Top 20 Peaks、計算峰高 (Peak Height) 與峰面積 (Peak Area)。
- 📥 **一鍵導出報表**：一鍵導出標準 CSV 或包含摘要、峰值與原始數據點的多分頁 Excel 檔。
- 🌐 **區網共享支援**：自動搜尋可用 Port (Fallback) 並顯示本機與區網 IP 地址，方便同辦公室電腦共享連線。

---

## 📁 檔案結構樹 (File Tree)

```
agilent-gc-lc-viewer/
├── README.md                           # 人類閱讀說明書
├── SKILL.md                            # AI 助理閱讀與指令手冊
├── setup_env.ps1                       # 一鍵環境自動設定腳本
├── 點我啟動Agilent數據解析器.bat         # 通用一鍵啟動腳本
├── ch_parser.py                        # Agilent .ch 二進位解析與尋峰核心引擎
├── main.py                             # FastAPI 後端與 API 伺服器
└── templates/
    └── index.html                      # HTML5/CSS3/Chart.js 網頁前端 Dashboard
```

---

## 🚀 跨電腦一鍵啟動步驟

1. 雙擊執行 **`點我啟動Agilent數據解析器.bat`**。
2. 系統會自動檢查並安裝缺少的 Python 套件。
3. 啟動成功後，瀏覽器會自動開啟 `http://localhost:8008` (或自動切換之 Port)。
4. 將 `.ch` 檔案或包含 `.D` 資料夾的 ZIP 檔拖入網頁即可進行分析與匯出。
