# 🎙️ AI 面試語音特質與資材適性分析系統 (Interview Analyzer)

本系統為專為 **HR 人資團隊與資材部門主管** 設計的現代化 AI 面試語音轉譯、個人特質 (DISC & Big Five) 評估與報告匯出系統。

---

## 🌟 核心功能亮點

1. 📋 **事前履歷 AI 分析與提問擬定 (Pre-interview Analysis)**
   * 支援上傳 PDF、圖片 (如 104 履歷截圖/掃描檔) 或直接複製履歷文字。
   * 自動比對應徵職能 (如【彰濱廠區】助理管理師、資材工程師等)，產出學經歷匹配評分、三大優勢、技能落差、職涯歷練與通勤轉折風險。
   * **自動擬定 4~6 個結構化面試提問題目**，含提問目的與面試官觀察重點指南，並支援一鍵下載 Pre-interview Word 評估報告。

2. ⚡ **長面試背景分段自動備份 (Chunked Auto-Save)**
   * 支援 1 小時以上的長面試，預設每 5 分鐘自動將語音片段備份至伺服器並即時拼接轉寫。
   * **零等待**：點擊結束錄音時無需等待整大段檔案傳輸。
   * **防斷電防遺失**：錄音檔案與逐字稿即時落盤保存。

3. 🎯 **資材與跨部門黃金 DISC 適性評估**
   * 內建資材部門專屬適性指標：
     * **現場助理工程師**：黃金 CS 型 (C型60% + S型40%) —— 著重料號精準度與現場 SOP 備料。
     * **資材工程師**：黃金 CS 型 (C型70% + S型30%) —— 著重 BOM 表結構分析與供需規劃。
     * **資材行政專員**：黃金 SC 型 (S型60% + C型40%) —— 著重跨部門溝通與 ERP 輸入零失誤。
   * 支援選單切換研發、業務、生產與通用跨部門評估。

4. 📄 **一鍵導出 Excel (.xlsx) 與 Word (.docx) 雙格式報告**
   * 支援將「事前履歷評估」與「現場面試與逐字稿評估」一鍵導出為精美 Excel (`.xlsx`) 試算表或 Word (`.docx`) 報告。
   * 報告內含：事前履歷分析報告與二面/現場面試評估報告，包括基本資料摘要、**DISC 全類型說明對照表 (自動高亮受訪者類型)**、Big Five 五大人格評估、提問指南與錄音逐字稿。

5. 📊 **獨立 PDF / 履歷圖片直接轉換為 Excel 試算表 (.xlsx)**
   * 內建獨立轉檔工具：無需經由 AI 進行面試分析，可直接將上傳之 104 履歷 PDF、圖片或掃描檔，完整將全文字、學經歷、職掌、自傳與細節 100% 萃取轉譯導出為標準 Excel 活頁簿 (`.xlsx`)。

6. 🔑 **多組 Gemini API Key 輪替與 Flash 模型 Cascade**
   * 支援貼入多組 Google AI Studio Free Tier Key，自動進行 Round-Robin 輪替與 Rate-Limit 容錯。
   * 自動降階支援：`gemini-3.6-flash` -> `gemini-3.5-flash` -> `gemini-3.1-flash-lite` -> `gemini-3-flash` -> `gemini-2.5-flash`。

7. 🗑️ **歷史紀錄與檔案管理與斷網重辨識**
   * 內建歷史紀錄資料庫，支援事前履歷分析報告與現場語音面試紀錄查詢、導出 Excel/Word 與一鍵刪除。
   * 支援「斷網補救重新辨識」：可隨時讀取本機音檔重新由 AI 解析。

---

## 📁 專案檔案結構

```
interview_analyzer/
├── 雙擊點我啟動面試語音AI分析系統.bat   # Windows 零硬編碼一鍵啟動腳本
├── main.py                             # FastAPI 後端伺服器 (具備動態 Port 與區網 IP 偵測)
├── docx_generator.py                   # Word (.docx) 評估報告自動產生器
├── generate_docx_samples.py            # 範例報告生成工具
├── setup_env.ps1                       # PowerShell 自動化安裝腳本
├── SKILL.md                            # AI 助理維護與安裝說明
├── requirements.txt                    # Python 套件依賴檔
├── static/
│   └── index.html                      # 現代化深色 Glassmorphism 前端網頁介面
└── data/
    ├── db.json                         # 面試紀錄資料庫 (JSON 格式)
    └── audios/                         # 錄音檔實體儲存目錄 (.webm)
```

---

## 🚀 如何在任何電腦上執行

本專案採用 **動態相對路徑 (%~dp0)** 設計，不論放在 C 槽、D 槽、隨身碟 (USB) 或網路磁碟，皆可 100% 直覺啟動：

### 方法一：一鍵雙擊啟動 (推薦)
1. 直接雙擊執行 `雙擊點我啟動面試語音AI分析系統.bat`。
2. 系統將自動檢查環境，並自動為你喚起預設瀏覽器連至 `http://localhost:8000`。

### 方法二：指令列啟動
```bash
# 1. 安裝套件
pip install -r requirements.txt python-docx

# 2. 啟動伺服器
python main.py
```

* **本機存取**：`http://localhost:8000`
* **區域網路共用**：`http://[你的本機IP]:8000` (方便同辦公室同仁一起使用)
