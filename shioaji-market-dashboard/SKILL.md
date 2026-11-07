# 永豐 Shioaji 即時看盤儀表板 (AI Agent 技能說明)

本專案為永豐金證券 Shioaji API 本地端看盤終端系統，專門解決傳統 Google Colab 方案「金鑰憑證上傳資安風險」、「閒置斷線」與「前端陽春」之三大缺陷。

---

## 1. 專案基礎資訊
- **專案名稱**：永豐 Shioaji 即時看盤儀表板 (AGY Edition)
- **實體路徑**：`C:\GOOGLE ANGET\shioaji-market-dashboard`
- **技術棧**：
  - 後端：Python 3.10+ / FastAPI / Uvicorn / WebSockets / python-dotenv
  - 前端：HTML5 / CSS3 (Dark Terminal Theme) / TradingView Lightweight Charts 4.x
  - 核心套件：`shioaji` (永豐金證券官方 SDK) / 內建模擬撮合引擎
- **預設服務位址**：`http://localhost:8088` (具備 Port Auto-Fallback 機制)

---

## 2. 核心檔案職責
| 檔案 | 職責說明 |
|---|---|
| `server.py` | FastAPI 主程式，提供 REST 狀態/歷史 K 線 API、WebSocket 即時 Tick 廣播，並內建台股幾何布朗運動高仿真模擬引擎 |
| `static/index.html` | 專業看盤終端主頁，採三欄式佈局（觀察清單、TradingView K線總覽、最佳五檔與逐筆明細） |
| `static/app.js` | 處理 TradingView 圖表初始化、WebSocket 連線維持、即時報價更新與五檔委託渲染 |
| `static/style.css` | 彭博終端風格之深色主題，台股習慣漲紅跌綠配色，動態長條圖與流暢微動畫 |
| `啟動看盤儀表板.bat` | 通用模板啟動腳本，自動偵測 Python、確認 pip 套件、自動處理 Port 佔用並開啟瀏覽器 |
| `setup_env.ps1` | 一鍵自動部署與依賴套件安裝腳本 |
| `requirements.txt` | 後端核心依賴清單 |
| `.env.example` | 永豐 API 金鑰與模式配置範本 |

---

## 3. AI 代理指引規範 (Agent Guidelines)
1. **環境檢查優先**：進入此專案時，若使用者欲啟動系統，優先引導或執行 `啟動看盤儀表板.bat` 或 `setup_env.ps1`。
2. **雙軌模式識別**：
   - 當無 Shioaji 金鑰或 `shioaji` 套件尚未安裝時，系統自動啟用 `SIMULATION` 模擬盤，所有功能（K線、五檔、逐筆、自選股切換）100% 完整可用。
   - 若使用者提供金鑰，引導使用者將金鑰存入 `.env` 或於前端「⚙️ 設定」彈窗填入，**嚴格遵守 Rule 2：絕對禁止將金鑰提交至 Git 倉庫**。
3. **客製化指標擴充**：
   - 若使用者要求新增技術指標（如 MA 均線、RSI、MACD、布林通道），直接於 `static/app.js` 透過 Lightweight Charts 擴充指標圖層即可。
