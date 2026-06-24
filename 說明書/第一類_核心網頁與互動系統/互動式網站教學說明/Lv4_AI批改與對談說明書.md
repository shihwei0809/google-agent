# Level 4 & Level 5：AI 即時批改與對談 - 使用說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent](https://github.com/shihwei0809/google-agent)


---

## 📝 模組概述
本模組展示了將 **AI 大語言模型 (Gemini API / Groq API)** 導入教學現場的完整架構。
*   **Level 4 (AI 批改免登入)**：學員撰寫簡答/問答題，提交後後端即時向 AI 發送請求，AI 根據提示詞（規準）給出分數與修改建議，但做完即丟不存檔。
*   **Level 5 (AI 全端一條龍)**：結合 AI 批改與長期資料庫儲存。AI 的批改分數與分析結果，會自動寫入 Firestore 資料庫中，累積為個人的長期學習歷程。
*   **對談模式 (Chat Tutor)**：使用多輪對話歷史陣列 (Chat Context)，實現一個具有教學引導性的 AI 技術助教。

---

## 🔒 技術關鍵：後端安全中轉（API Proxy）
這是本專案最核心的安全防護設計：**絕對不能在瀏覽器前端直接呼叫 API**，否則 API 金鑰 (API Key) 會在 F12 的網路 (Network) 標頭中被學員隨手複製。

本系統的後端安全轉發設計如下：
```
[前端瀏覽器] ──(呼叫 /.netlify/functions/groq-chat)──> [Node.js 後端 (server.js)]
                                                            │
                                                  (讀取 .env 中的金鑰，中轉)
                                                            ▼
                                                     [Groq 官方 API]
```

---

## 🛠️ 檔案位置與實作

*   **後端代理邏輯**：`互動式網站/server.js` 中的 `/api/groq-chat` 與 `/api/ask-ai` 路由。
*   **AI 批改問答頁面**：`互動式網站/lv4-netlify-ai.html`
    *   *提示：在網址後方加入 `?level=5` 參數即可切換為 Level 5 模式，開啟姓名欄位與本地 Firebase 模擬學習歷程日誌。*
*   **AI 多輪對談頁面**：`互動式網站/chat-tutor.html`

---

## 🚀 測試與操作步驟

### 1. 本地啟動伺服器
1.  確保 `互動式網站` 根目錄下的 `.env` 配置了 `GROQ_API_KEY` 或 `GEMINI_API_KEY`。
2.  執行 `node server.js`。

### 2. 測試 AI 簡答題批改
1.  開啟 [http://localhost:8888/lv4-netlify-ai.html](http://localhost:8888/lv4-netlify-ai.html)。
2.  在問答題輸入答案（例如：「Level 4用完即忘，Level 5會將評語分數存入Firebase中」）。
3.  點擊「**提交並由 AI 即時批改**」。
4.  系統將會回傳由 AI 產生的分數與具體建議。

### 3. 測試 AI 即時對談 (Chat Mode)
1.  開啟 [http://localhost:8888/chat-tutor.html](http://localhost:8888/chat-tutor.html)。
2.  在下方輸入問題發送，AI 助教將會進行繁體中文回應，並在每次回答完後，自動提出一個引導性的追問問題以幫助您深造！
