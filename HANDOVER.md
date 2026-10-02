# 跨機開發交接日誌 (HANDOVER)

## 2026-10-02 交接事項
- **前次進度與狀態**：針對「溫度通報系統」Cloudflare D1 版本，完成排程定時器 (Cron Triggers) 的雙引擎架構與防呆機制設定。
- **今日遇到的錯誤與解決步驟**：
  1. **雙邊觸發導致資料重複**：當 GAS 定時器與 Cloudflare Cron 同時喚醒時，會產生兩筆相同的氣象觀測紀錄。解法：在 Cloudflare check.js 中新增針對 obs_time 的 SQL deduplication (防呆機制)。
  2. **編碼亂碼問題復發**：使用 Python 腳本更新 check.js 時意外覆寫出 CP950 亂碼，導致 Cloudflare 無法正常顯示狀態文字。已透過 PowerShell 原生 UTF-8 $js = @"..."@ 的方式重新產生乾淨程式碼並成功部署。
  3. **Cloudflare 自動佈署中斷**：因專案為 Monorepo，Cloudflare 未自動偵測到目錄變更導致排程與新版程式碼未上線。解法：引導使用者進入 Cloudflare 控制台手動執行「建立部署」。
  4. **通訊頻道分流**：為了達成「Google Sheets 與 D1 雙重紀錄，但不重複發 LINE」，引導使用者將 GAS 的 LINE 廣播區塊註解，並把 監測頻率 設為 10 分鐘，實現了「GAS 寫表格、發信，Cloudflare 寫 D1、發 LINE」的完美雙引擎運作。
- **後續待辦事項**：
  1. 確認「手動強制測試」按鈕在 PWA 網頁上的功能是否需要正式接通至 Cloudflare API (目前由 GAS 試算表選單擔任此功能)。
  2. 觀察接下來的 10 分鐘，防呆機制是否如期將重複的 obs_time 紀錄捨棄。

## 2026-10-01 交接事項
- **前次進度與狀態**：將原先於 Firebase 與本機端 Python 運行的溫濕度系統，正式移植至 Cloudflare Pages + D1 雲端架構。
- **今日遇到的錯誤與解決步驟**：
  1. **前端快取死結**：PWA 的 Service Worker (sw.js) 未加上 self.skipWaiting() 導致前端頁面卡在舊版。修正 sw.js 並升級快取版號解決。
  2. **編碼亂碼問題**：以 PowerShell 取代大量文字時導致 app.js 與 Code.gs 變成 CP950。改以 Node.js / UTF-8 原生寫入解決。
  3. **Cloudflare 時區停滯**：D1 自動生成的 timestamp 為 UTC，導致 ORDER BY timestamp DESC 把本地時間 (UTC+8) 的歷史資料排到前面。改以 JavaScript 寫入帶有台北時區之 timestamp 字串解決。
  4. **歷史查詢功能損壞**：移植時遺漏了歷史圖表的查詢按鈕與對應之 JS 邏輯 (queryHistoricalChartData)，以及 ID 綁定錯誤。已修復並支援區間查詢與圖表動態標題。
  5. **警報視覺效果遺失**：修正 app.js 動態變色邏輯，恢復接近閾值 (1.5度內) 顯示橘色、超過顯示紅色的介面提示。
  6. **定時喚醒機制脫鉤**：GAS 端修改的 Code.gs 未存檔導致 Cloudflare 端點沒有被定時觸發。
- **後續待辦事項**：
  1. 確保 Cloudflare 可以穩定每分鐘獲得最新資料（無論是透過 GAS 定時器或是 Cloudflare Cron Triggers）。
  2. 如果使用者選擇廢棄 GAS，需要設定 Cloudflare 定時器。
