# 交接日誌 (HANDOVER)

## 前次進度與交接事項
- 完成了 D1 資料庫遷移與帳號管理後台實作。
- 遭遇 Windows PowerShell 編碼問題導致 D1 資料庫欄位被寫入 Big5 亂碼，已撰寫專屬修復腳本清空並重設 \System_Config\。
- 發現並解決了因瀏覽器快取舊版 \dmin.html\ 導致設定被覆蓋的問題。
- 操作手冊已更新，說明 QC 實名制登入與後台解鎖雙軌 PIN 碼（預設 8888）之不同。

- **【重要坑點】Cloudflare 部署機制**：qc-samples 目前在 Cloudflare 上是「直接上傳 (Direct Upload)」專案，沒有連結 Git。推送到 GitHub main 分支**不會**自動更新 qc-samples，只會更新 eshine-package 等其他專案。因此，任何針對 QC 系統的修改，除了推送到 GitHub 備份外，**必須強制在本機執行 
px wrangler pages deploy ./ --project-name qc-samples** 才能真正上線。

## 下一步待辦清單
- 觀察上線後，使用者是否能在 PWA 環境中順利使用帳號密碼登入並完成檢驗判定。
- 確保 Teams Webhook 推播功能正常執行。

