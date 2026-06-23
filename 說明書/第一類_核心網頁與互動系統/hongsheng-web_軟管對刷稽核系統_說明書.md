# 軟管對刷稽核系統 (hongsheng-web) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/hongsheng-web](https://github.com/shihwei0809/google-agent/tree/main/hongsheng-web)


## 專案簡介
本專案為鴻勝化學的「軟管對刷稽核系統 — 互動式教育訓練與模擬演練」網頁應用程式。旨在幫助現場操作員通過暗黑科技風格的介面，進行模擬演練與 QC 檢驗培訓。

## 主要功能特色
- **科技感 UI 設計**：採用深色模式、霓虹光暈與動態掃描線視覺效果。
- **即時連線狀態**：前端與 Firebase Firestore 實時連線，並設有連線狀態指示燈。
- **雙模式切換**：
  - **簡報模式**：用於講授軟管對刷與稽核的理論知識。
  - **模擬演練模式**：模擬現場條碼掃描、操作員手動配對確認、以及 QC 儀表板檢驗流程。
- **防錯警示系統**：實時比對刷卡資訊與預計配對，如出錯會觸發紅色警示燈與警告音效。

## 技術棧
- 前端：HTML5, CSS3 (Vanilla), JavaScript (ES6)
- 後端資料庫：Firebase Firestore

## 本機執行與操作
1. 按兩下開起 `hongsheng-web/index.html` 即可單機運行。
2. 若需實時 Firebase 連線，請確保 `.env` 或 `app.js` 中配置了正確的 Firebase API 金鑰。
3. 進入網頁後，點選右上角的 **「開始演練」**，依序執行條碼掃描與對刷稽核操作。
