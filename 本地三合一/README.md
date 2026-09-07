# 台積三合一單與 COA 雙重核對系統 (GAS 雲端智慧辨識版)

本系統專為台積電槽車出貨檢驗設計，採用 Google Apps Script (GAS) Web App 雲端無伺服器架構，支援現場手機、平板及電腦端免安裝即時操作。透過高精度 Google Cloud Vision OCR 與 Gemini 多模型瀑布流備援技術，結合嚴格的「四重關卡」安全卡控比對邏輯，於 2~3 秒內自動完成三合一單、COA 檢驗報告與地磅單據之防呆核對，杜絕人為疏失。

---

## 核心功能列表
- **雙重輸入支援**：支援手機相機秒讀三合一單 QR Code，或透過「AI 讀單」拍照正則解析標籤文字。
- **雙重 OCR 瀑布流高可用架構**：
  - 主力：Google Cloud Vision API（支援雙金鑰自動切換，達 900 次閥值自動輪替）。
  - 備援：Gemini 多模型瀑布流（gemini-3.6-flash → 3.5-flash → 3.5-flash-lite → 3.1-flash-lite），大出貨量永不斷線。
- **四道嚴格防呆比對邏輯**：
  1. **COA 批號核對**：截取 1~11 碼主批號，具備 OCR 模糊容錯 (3↔5, 8↔B, O↔0 等)。
  2. **送達地點 8 碼拆分**：自動去除前綴 `E`，嚴格拆分前 4 碼「廠別」與後 4 碼「廠區」雙重同時相符判定。
  3. **地磅槽號反干擾核對**：比對槽號前主動自文字抽離批號字串，防止長批號內部字元造成槽號誤判。
  4. **地磅畫面批號比對**：核驗當前磅單掛入車次之生產批號一致性。
- **單號智慧自動抽取**：自動以正則表達式提取來源單號 (`ESXM1...`) 與磅單編號 (`ESXM2...`)。
- **雙月自動滾動分頁與雲端存證**：自動按月份雙月建立 `Data_YYYY_MM-MM` 分頁，照片直存 Google Drive 備份資料夾並生成直連網址。
- **完整查詢與匯出系統**：支援關鍵字全文檢索、日期區間過濾、高解析佐證照片調閱及一鍵匯出 UTF-8 BOM CSV。

---

## 檔案結構說明 (File Tree)
```text
本地三合一/
├── README.md                           # 專案說明文件 (此檔案)
├── SKILL.md                            # AI 代理指南與環境說明
├── setup_env.ps1                       # 一鍵環境配置 PowerShell 腳本
├── build_manual_doc.py                 # 自動生成圖文手冊腳本 (產出 docx 與 pdf)
├── 程式碼_V2_動態讀取版.gs               # GAS 後端主邏輯 (動態金鑰/瀑布流/四重比對)
├── 程式碼_Backup.gs                    # GAS 歷史程式碼備份
├── Index_Backup.html                   # 前端 Web App 介面 (HTML5/Tailwind/QR Scanner)
├── 三合一單與COA雙重核對系統_操作手冊.docx # 繁體中文 Word 操作手冊 (本機 Word 格式)
└── 三合一單與COA雙重核對系統_操作手冊.pdf  # 繁體中文 PDF 操作手冊
```

---

## 快速啟動與手冊生成
1. **生成操作手冊**：
   ```powershell
   python build_manual_doc.py
   ```
2. **部署至 Google Apps Script**：
   - 建立新的 Google 試算表。
   - 開啟「擴充功能」>「Apps Script」。
   - 將 `程式碼_V2_動態讀取版.gs` 貼入 `程式碼.gs`，將 `Index_Backup.html` 貼入 `Index.html`。
   - 執行 `setupConfigSheet()` 自動建立 `設定` 與 `API_Log` 分頁並填入金鑰。
   - 點擊「部署」>「新增部署作業」> 類型選取「網頁應用程式」，將存取權設為「所有人」。
