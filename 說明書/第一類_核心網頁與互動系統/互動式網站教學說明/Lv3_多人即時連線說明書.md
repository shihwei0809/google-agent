# Level 3：多人即時同步連線 - 使用說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/互動式網站](https://github.com/shihwei0809/google-agent/tree/main/互動式網站)


---

## 📝 模組概述
本模組重現了三師爸「**互動教學駕駛艙**」的核心多人同步機制。
將系統完全分離為：
1.  **講師投影幕端 (Tutor View)**：控制投影片翻頁、推播題目，並在大螢幕上即時以圓形統計圖 (Donut Chart) 累計學生票數。
2.  **學員答題端 (Student View)**：同步追隨講師投影片，若講師進入測驗，自動彈出答題卡並提交。

*   **解決的痛點**：克服 Google Sheets 等傳統 API 的寫入瓶頸，提供秒級的即時數據處理，避免班級多人同時提交時卡死。
*   **技術原理**：在正式環境使用 Firebase Firestore 的 `onSnapshot()` WebSocket 連線監聽；在本機環境則使用我們為您寫好的 Node 本機同步伺服器 (`server.js`) 進行資料交換。

---

## 🛠️ 技術實作與程式架構

### 檔案位置
*   **講師端頁面**：`互動式網站/lv3-tutor.html`
*   **學員端頁面**：`互動式網站/lv3-student.html`
*   **同步伺服器**：`互動式網站/server.js`

### 同步運作流程 (Polling Mechanism)
本機環境下，學員端與講師端每 500 毫秒向本地 Node 服務 `GET /api/class-state` 查詢當前狀態：
1.  **講師翻頁**：講師在 `lv3-tutor.html` 翻到第 $N$ 頁 $\rightarrow$ 發送 `POST /api/class-state` 將 `currentSlide` 設為 $N$ $\rightarrow$ 學員端 `lv3-student.html` 在 500ms 內檢測到變化，自動轉頁。
2.  **學員提交**：學員提交選項 $\rightarrow$ 發送 `POST /api/submit-answer` $\rightarrow$ 伺服器將該選項累加 $\rightarrow$ 講師端在 500ms 內讀取新數據，**Conic-Gradient 圓餅圖即時動態重繪**。

---

## 🚀 操作測試指南

### 第一步：啟動本機同步伺服器
打開終端機，執行：
```bash
node server.js
```

### 第二步：開啟講師端與學員端分頁
1.  在瀏覽器開啟 **講師端**：[http://localhost:8888/lv3-tutor.html](http://localhost:8888/lv3-tutor.html)
2.  點擊右上角「**複製學生端連結**」，並開啟一個**無痕視窗分頁**貼上（或使用手機掃描區域網址連線）：[http://localhost:8888/lv3-student.html](http://localhost:8888/lv3-student.html)

### 第三步：測試即時互動效果
1.  在學員端輸入暱稱（如：小明），點擊進入互動室。此時會顯示「講師正在講授投影片中...」。
2.  回到講師端，點擊左側選單的「**3. 測驗 Q2: 喜愛的運動**」。
3.  切回學員端，你會發現畫面**已自動秒級同步跳轉**，並出現 A/B/C 三個答題按鈕。
4.  在學員端點擊「B) 足球」，點擊送出。學員端會即時出現綠色答對框與詳解。
5.  此時看向講師端大螢幕，**總票數會立刻從 0 變為 1，圓形圖自動繪製出 B 選項佔比 100% 的區塊**！
6.  講師可點擊「**重置本題答題**」讓全班重新作答。
