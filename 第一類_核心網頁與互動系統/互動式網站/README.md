# 🎨 互動式網站與隨堂同步互動系統 (Interactive Web Training Hub)

本專案是配合三師爸（Sensebar）「寫教學應用程式的五個等級」概念所設計的本地互動式網頁與即時同步教學系統。

## 🌟 核心功能亮點

*   **五個等級完整實作**：包含從 Level 1 純前端網頁、Level 2 Google 試算表後端、Level 3 即時同步課堂、Level 4 AI 即時批改，到 **Level 5 AI 即時課程生成與多人同步**。
*   **0% 依賴本地伺服器 (`server.js`)**：使用 Node.js 原生模組，不需下載任何 npm 套件，極速啟動！支援 API 密鑰安全代理與中轉。
*   **PDF/TXT 教材一鍵生成簡報與測驗**：在 Level 5 講師端，上傳 PDF 或 TXT 教材後，Gemini 2.5 Flash 自動解析並生成 5-10 頁的投影片與互動測驗。
*   **雙端即時秒級同步**：講師端翻頁時，所有學生端畫面秒級同步更新；學生提交答案時，講師端 Donut 圓餅圖即時呈現統計。
*   **AI 智能對談助教**：整合 Groq API 的多輪對話聊天助教，幫助學生解答問題。

## 📂 檔案目錄結構

```text
C:\GOOGLE ANGET\第一類_核心網頁與互動系統\互動式網站\
├── .env                  # 金鑰組態設定 (GROQ_API_KEY, GEMINI_API_KEY)
├── index.html            # 專案大廳 (能力階梯首頁入口)
├── server.js             # 0% 依賴的本地 HTTP & WebSocket 模擬伺服器
├── README.md             # 專案說明書 (本檔案)
├── SKILL.md              # AI 助理技能描述檔案
├── setup_env.ps1         # 環境偵測與安裝腳本
│
├── lv1-frontend.html     # Level 1: 純前端作答 (不保存)
├── lv2-sheets.html       # Level 2: 雲端 Google 試算表寫入
├── lv3-tutor.html        # Level 3: 多人同步 - 講師投影幕端
├── lv3-student.html      # Level 3: 多人同步 - 學生作答端
├── lv4-netlify-ai.html   # Level 4: Serverless + AI 簡答評分
├── lv5-tutor.html        # Level 5: AI 教材生成 + 多人即時同步講師端 (新增)
├── lv5-student.html      # Level 5: AI 教材生成 + 多人即時同步學生端 (新增)
│
├── chat-tutor.html       # 額外收錄: Groq 多輪對談 AI 助教
├── teaching-cockpit.html # 額外收錄: 兩欄式靜態教學駕駛艙
└── netlify/              # Netlify Edge Functions 配置與代理中轉函數
```

## 🚀 跨電腦一鍵啟動與執行步驟

1.  **環境確認**：確保本機已安裝 **Node.js**。
2.  **設定 API 金鑰**：在 `.env` 中加入您的 API 金鑰：
    ```env
    GROQ_API_KEY=your_groq_key
    GEMINI_API_KEY=your_gemini_key
    ```
3.  **啟動本地伺服器**：
    打開終端機（cmd 或 PowerShell），進入本目錄並執行：
    ```bash
    node server.js
    ```
4.  **開啟瀏覽器**：
    直接開啟：[http://localhost:8888](http://localhost:8888) 即可體驗完整功能。
