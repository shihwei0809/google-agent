# 跨機交接日誌 (HANDOVER)

## 今日進度與交接事項 (2026-11-08 回收液入料系統全面整合 Cloudflare R2 物件儲存，徹底解除 Google Drive 20GB 配額限制)
- **開發專案**：回收液入料記錄系統 (`3_Cloudflare_D1版`)
- **核心目標**：解決 Google One 若未續約降為 20GB 導致照片上傳受限問題，將照片由 Google Drive / GAS 改為存入 Cloudflare R2。
- **完成項目**：
  1. **建立 R2 儲存桶**：於 Cloudflare 建立 `recycle-photos` R2 Bucket。
  2. **配置 wrangler.toml 綁定**：新增 `[[r2_buckets]] binding = "PHOTOS" bucket_name = "recycle-photos"`。
  3. **實作 R2 照片上傳 API (`/api/upload`)**：
     - 支援 Base64 Data URL 解析與 Uint8Array 二進位轉譯。
     - 將照片直接存入 R2 (`env.PHOTOS.put`)，並傳回靜態讀取路徑 `/api/photos/${key}`。
     - 自動更新 D1 `recycle_records` 之照片欄位 (`t_before_url`, `v_photo_url`, `t_after_url`)。
  4. **實作 R2 高速照片代理與快取串流 API (`/api/photos/[[path]]`)**：
     - 支援 GET / HEAD 請求與 ETag 304 邊緣極速快取。
     - 設定 `Cache-Control: public, max-age=31536000, immutable`，全域 CDN 邊緣加速。
  5. **升級前端整合 (`public/index.html` v18-D1)**：
     - 送出入料前/入料後時，照片直接上傳至 `/api/upload` (R2)，免除 GAS 上傳負擔。
     - 背景 `autoSync` 離線重試佇列同步升級至 R2 + D1。
     - Google Apps Script 僅保留純文字資料備份，不再傳輸任何照片 Base64，對 Google Drive 的空間消耗歸零 (0 Bytes)！
  6. **PWA Service Worker 快取推進**：
     - `sw.js` 推進至 `recycle-d1-v18-r2-photos-sync`，主動觸發現場裝置更新。
  7. **後台刪除防呆清理**：
     - 在 `/api/records` 刪除記錄 (`delete_record`) 時，同步清理 R2 中的對應照片。

---

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
- **避坑指南**：
  - R2 儲存桶命名建議採小寫英數與減號（如 `recycle-photos`）。
  - Cloudflare Pages Functions 綁定 R2 時，在 `wrangler.toml` 宣告 `[[r2_buckets]]`，並可在 Cloudflare Pages 後台「設定 -> 函數 -> R2 儲存貯體繫結」確認綁定為 `PHOTOS`。
