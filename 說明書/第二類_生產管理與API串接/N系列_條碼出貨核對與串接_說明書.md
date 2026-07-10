# N系列 條碼出貨核對與串接 - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/N系列BARCODE出貨核對](https://github.com/shihwei0809/google-agent/tree/main/N系列BARCODE出貨核對)

## 專案簡介
本系統專為 N 系列產品出貨設計，提供手持掃描槍/網頁端條碼對刷與核對，驗證「現場桶槽」、「四合一標籤」與「繳庫單」的一致性，防堵人為出貨錯誤。

## 主要功能特色
- **實時核對**：掃描後立即在畫面比對出貨型號與數量，防止重複掃描、混批。
- **Teams Webhook 異常通知**：當巡檢核對失敗（例如批號/料號不符、貼紙錯誤或格式不符），或是雲端系統寫入錯誤時，系統會自動發送警報至指定的 Microsoft Teams 頻道。
- **API 自動同步**：手機 App 端離線核對成功後，可批次將記錄上傳並寫入 Google 試算表。

## 技術棧
- Google Apps Script (GAS), HTML, CSS, JavaScript, Microsoft Teams Webhook

## 配置說明
- **Teams Webhook 網址設定**：
  1. 可在 GAS 專案設定中的「指令碼屬性」新增 `TEAMS_WEBHOOK_URL` 鍵值。
  2. 或在專案試算表中，新建名為「系統設定」的工作表，在 A1 輸入 `Teams Webhook URL`，B1 貼上網址。

## 操作步驟
1. 打開出貨核對網頁（或使用 APK 掃描端）。
2. 依序掃描「現場桶槽」、「四合一標籤」、「繳庫單」上的產品與批號條碼。
3. 點選「巡檢核對並存檔」，若核對相符則自動寫入資料庫；若不符則彈出警報，並即時通報 Teams 頻道。
