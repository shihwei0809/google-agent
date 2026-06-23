# 互動式教學系統 - 全面操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent](https://github.com/shihwei0809/google-agent)


本專案是一個基於「用 AI 打造互動教學網頁五個階段」所開發的教學套件本機實作版本。旨在幫助講師/訓練官建立高互動性的數位課堂，提升人員訓練效率。

---

## 📂 專案說明書目錄

我們已將各模組的操作說明進行了拆分整理，您可以點選以下連結查看各等級的詳細程式架構與配置方法：

1. 📖 **[Lv.1 純前端單機版說明書](Lv1_純前端說明書.md)**
   * 無須伺服器與資料庫，單機即時判定單選題對錯。
2. 📖 **[Lv.2 Google 試算表連線說明書](Lv2_Google試算表說明書.md)**
   * 前端 fetch 透過 GAS (Google Apps Script) 後端代理，自動將學員作答紀錄寫入雲端 Google 試算表。
3. 📖 **[Lv.3 多人即時同步連線說明書](Lv3_多人即時連線說明書.md)**
   * 「講者大螢幕 (Tutor View)」與「學員答題端 (Student View)」分離，實現秒級同步翻頁與圓餅圖計票結果實時渲染。
4. 📖 **[Lv.4 & Lv.5 AI 即時批改與對談說明書](Lv4_AI批改與對談說明書.md)**
   * 後端安全代理 (Serverless) 防護金鑰，串接 Groq/Gemini API 進行問答題批改與多輪語意對話。

---

## 🚀 本地開發伺服器啟動與操作指南

為了讓本地環境的「多人即時連線 (Lv.3)」以及「AI 後端安全代理 (Lv.4)」能正常運作，本專案內置了一個 **零依賴的 Node.js 伺服器 (`server.js`)**。

### 第一步：金鑰配置
在 `互動式網站` 根目錄下，確認 `.env` 檔案內包含以下金鑰配置：
```env
GROQ_API_KEY=gsk_your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 第二步：啟動本機伺服器
打開終端機 (PowerShell/CMD)，進入 `互動式網站` 專案目錄，執行以下指令：
```bash
node server.js
```
看見 `🚀 本地開發伺服器啟動成功！` 後，代表伺服器已在本地 **Port 8888** 監聽。

### 第三步：開啟瀏覽器操作
*   **主入口網頁**：`http://localhost:8888/index.html`
*   **教學駕駛艙 (Lv.3 講者端)**：`http://localhost:8888/lv3-tutor.html`
*   **學員答題端 (Lv.3 學員端)**：`http://localhost:8888/lv3-student.html`
*   **AI 安全對談助教**：`http://localhost:8888/chat-tutor.html`
