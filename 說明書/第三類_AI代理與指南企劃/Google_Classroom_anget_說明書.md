# Google Classroom Agent - 操作說明書

> 🔗 **GitHub 專案庫**：[mathruffian-dot/classroom-agent-kit](https://github.com/mathruffian-dot/classroom-agent-kit)


## 專案簡介
本專案為一個自動化 AI 代理服務，串接 Google Classroom API，能協助講師自動發布作業、管理學員作答、並自動批改上傳作業。

## 主要功能特色
- **Classroom 自動發課**：支援以 API 批次建立課程單元。
- **作業監控**：自動輪詢（Poll）學員繳交狀態，並在繳交時觸發 AI 進行初步評分。

## 技術棧
- Node.js, Google Classroom API, Google OAuth 2.0

## 操作步驟
1. 在專案目錄下配置 `credentials.json` (從 Google Cloud Console 申請)。
2. 本地執行：
   ```bash
   node server.js
   ```
3. 瀏覽器開啟 `http://localhost:3000` 進行 Google 帳號授權，即可啟動自動化管理。
