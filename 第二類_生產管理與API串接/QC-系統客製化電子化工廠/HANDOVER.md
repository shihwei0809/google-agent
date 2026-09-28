# QC 系統 跨電腦交接日誌 (HANDOVER.md)

## 最後更新：2026-09-29

---

## 📌 前次進度與交接事項

### 當前分支狀態
- **生產 main**：`ef8fd82` — feat: Add initAllSheets() to auto-provision all required GAS sheets on demand
- **備份分支 feat/20260928**：`31dc6a4` — End of day backup

### Cloudflare Pages 狀態
- **生產網址**：https://qc-samples.pages.dev
- **最後成功部署**：commit `b4dd852`（取樣重送數量修正）
- **Cloudflare Build watch path** 已設定：`第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/**`
  → 只有 D1 版檔案異動才觸發部署

---

## 🐛 今日遇到的問題與解決方式

### 1. index.html 全面亂碼（2361 個 PUA 字元）
- **原因**：舊 Python 腳本（commit `c3ef37c`）透過 PowerShell 用 `Set-Content` 寫入 UTF-8 檔案時破壞中文字元
- **解法**：
  - 用 `git show ba12d9a:"...index.html"` 將乾淨版本直接以 binary 讀出寫入
  - 之後一律用 Node.js `fs.readFileSync/writeFileSync('utf8')` 或 Python script file 對 `3_Cloudflare_D1版` 做 patch
  - 禁止用 PowerShell `Set-Content` 或 `Out-File` 操作含中文的 .html/.gs 檔

### 2. `1_Web_網頁版/Code.gs` 亂碼
- **原因**：該檔案是早期 Python 腳本生成，encoding 異常（Big5 存成 UTF-8 路徑）
- **解法**：直接把根目錄乾淨的 `Code.gs` binary 複製覆蓋

### 3. 取樣重送按鈕顯示 0 筆
- **原因**：`updateT100ButtonCounts()` 定義在全域 scope，讀不到 `render()` 的局部變數 `cData`
- **解法**：改用 `t100Orders.filter(o => { const sub = getOrderSubmissionInfo(o); return sub && sub.status === 'failed'... })` 計算

---

## ✅ 今日完成功能

| # | 功能 | 狀態 |
|---|------|------|
| 1 | 修復三個 index.html 的全面亂碼（2361 PUA 字元） | ✅ |
| 2 | 重新 apply T100 filter：退回件出現在待送樣放櫃 | ✅ |
| 3 | 新增 🔄 取樣重送 tab 按鈕（T100 篩選第4個選項） | ✅ |
| 4 | 標籤更名：`被退件需重送` → `品質不合格重取` | ✅ |
| 5 | 三個 tab 按鈕顯示即時數量徽章（今日/待送樣/取樣重送） | ✅ |
| 6 | 修正取樣重送按鈕計數邏輯（getOrderSubmissionInfo 全域算） | ✅ |
| 7 | GAS Code.gs 新增 `initAllSheets()` 一鍵補齊所有分頁 | ✅ |
| 8 | Cloudflare build watch path 只監聽 3_Cloudflare_D1版/** | ✅ |
| 9 | 修復 1_Web_網頁版/Code.gs 亂碼 | ✅ |

---

## 📂 重要檔案位置

| 檔案 | 路徑 |
|------|------|
| Cloudflare 後端 API | `3_Cloudflare_D1版/functions/api/index.js` |
| Cloudflare 前端 | `3_Cloudflare_D1版/index.html` |
| GAS 後端 | `1_Web_網頁版/Code.gs` (同 root `Code.gs`) |
| GAS 前端 | `1_Web_網頁版/Index.html` |
| PWA 前端 | `2_PWA_App版/index.html` |

---

## 🔜 下次繼續的事項

- [ ] 在 GAS 編輯器貼上最新 `Code.gs`（貼到 GAS 才會生效）
- [ ] 在 GAS 編輯器執行 `initAllSheets()` 補齊分頁
- [ ] 確認 Cloudflare 生產環境頁面可以正常顯示（之前空白畫面問題）
- [ ] 特採流程（需特採 → 待特採完成）的後端 API 尚未全面測試
