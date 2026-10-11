# 跨機交接日誌 (HANDOVER)

## 前次進度與交接事項
- **日期**：2026-10-11
- **開發專案**：回收液入料記錄系統
- **完成事項**：
  1. **iPhone 拍照效能優化**：加入 Canvas 前端等比縮放 (1280px) 與 JPEG 75% 壓縮，將照片從 8~15MB 降至 200~400KB，徹底消除連拍延遲卡頓。
  2. **離線與重複送出防呆強化**：
     - 新增 `complete_feed` API，當離線時前、後都在手機完成時，一次性打包寫入，避免拆分請求造成競態。
     - Google Apps Script 加入 `LockService.getScriptLock()` 排隊鎖，杜絕 1 秒內並行請求產生的重複列。
     - 前端加入 `r.isProcessing` 單筆傳輸鎖與資料完整性驗證（車號、前液位照、車輛照為必填；完成入料必須有後液位照）。
  3. **修復 UTC 跨時區 16:00:00 顯示問題**：在 GAS 與前端強制格式化為乾淨的 `yyyy-MM-dd` 日期字串。
  4. **PWA 離線連線與導航修復**：修正 `sw.js` (v9) 與 `manifest.json`，支援離線兜底（Offline fallback），解決安裝桌面開啟時出現 ERR_FAILED 哭臉畫面。
  5. **PWA 自動更新橫幅**：實作 Service Worker 背景自動檢查與雙向推播 (`VERSION_UPDATED`)，發布新版本時前端自動彈出綠色「點擊立即更新」橫幅，並將此規格納入 `INSTRUCTIONS.md` 全域規範。
- **未完事項 / 待觀察**：
  - 觀察現場手機端在弱網環境下照片壓縮與背景上傳流暢度。
- **避坑指南**：
  - PWA 在 iOS 與 Android 離線執行時，`start_url` 建議設定為 `./` 並於 Service Worker 加入 `navigate` 兜底，避免路徑轉向時引發 ERR_FAILED。
  - Google Apps Script 處理並行請求必須依賴 `LockService`，不可只靠 Sheets 讀取防重複。
