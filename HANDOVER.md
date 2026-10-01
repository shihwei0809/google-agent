# 跨電腦交接日誌 (HANDOVER)

## 前次進度與交接事項 (2026-10-01)
- **完成項目**：
  1. 解決了 TSC 標籤機因為 Windows 驅動高度設定錯誤導致的「印兩張」問題 (實體貼紙確認為 90x60mm)。
  2. 調整 index.html 的列印 CSS，關閉背景顏色避免熱感應印表機印出淡色網點，並重新設計簽名欄位底線。
  3. 完成「附加照片」功能 (方案 A: Google Drive + GAS)。在 Code.gs 中實作了 Base64 照片解碼上傳，並在 Cloudflare D1 的 QC_Samples 資料表中新增了 photoUrl 欄位與對應 API。
  4. 修復了網頁版 index.html 內的 Service Worker 快取名稱與腳本重複寫入的 SyntaxError，確保新版上傳按鈕與資料能夠正確顯示。
- **待解決/測試事項**：
  - 目前保留在 eat/20261001 分支，尚未發布正式 Tag。
  - 需要使用者確認照片上傳功能是否在跨裝置/手機上操作正常。
  - Cloudflare 的 PWA 快取已推進至 3.0.1，若還有舊版問題，需提醒使用者清除快取。
