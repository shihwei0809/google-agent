# 📋 跨電腦交接日誌 (HANDOVER.md)

> 每次收工由 AI 自動更新此檔案。開工時 AI 必須讀取並顯示給使用者。

---

## 📅 2026-09-06 交接紀錄（筆電收工）

### ✅ 今日完成事項

| # | 功能 | Commit | 狀態 |
|---|------|--------|------|
| 1 | **升級 AI 文字精修功能 + 前端讀取 Loading UI** | `748d15d` | ✅ 完成 |
| 2 | **修復 AI Prompt 旁白問題 + Markdown 圖片 URL 編碼錯誤** | `08febd5` | ✅ 完成 |
| 3 | 驗收所有訓練教材平台功能並完成 Release | `5e05896` | ✅ 完成 |

### 🔧 技術細節

1. **AI Prompt 旁白問題**
   - 發現 AI 在文字精修時會加入旁白（例如「以下是修改後的內容：」），導致輸出混入無關文字。
   - 修復：在 Prompt 明確指定「只輸出結果，不加任何前言或說明」。

2. **Markdown 圖片 URL 編碼**
   - 含中文字元的圖片路徑未做 URL encode，導致圖片載入失敗。
   - 修復：解析 ![...](…) 時對路徑自動套用 encodeURIComponent。

3. **前端讀取 Loading UI**
   - AI 精修期間前端無視覺回饋，使用者不知是否在處理中。
   - 修復：加入 Loading Spinner，精修開始顯示、完成後隱藏。

### 📌 給另一台電腦（公司）的接手指示

1. 執行 `git pull` 確保拉到最新的 main（含 v1.10.0~v1.10.2 Tags）。
2. 昨天修改集中在訓練教材平台的 AI 文字精修功能。
3. HANDOVER.md 空白是系統漏洞已修補，往後收工會強制確認有內容才 push。

---

## 📅 2026-09-05 交接紀錄（v1.9 正式發布）

| # | 功能 | 狀態 |
|---|------|------|
| 1 | 正式發布 v1.9 - PWA 雙軌架構 + eshine-package Cloudflare 部署 | ✅ |
| 2 | 修復 Git Submodule 殘留 160000 連結（Cloudflare Pages 克隆錯誤） | ✅ |
| 3 | 新增 Cloudflare Pages 完整部署架構疑難排解手冊（docx + pdf） | ✅ |
| 4 | 鴻勝包材管理系統 v13.5 導入 PWA 雙軌 | ✅ |
| 5 | 消除 Big5 亂碼（meta charset=UTF-8 + UTF8Handler） | ✅ |
| 6 | BAT 升級為純 ASCII 中繼 + run_server.py 架構 | ✅ |

### 🚨 避坑：Cloudflare SPA 絕對路徑鐵律
在 Cloudflare Pages SPA，所有跳轉連結一律用絕對路徑，禁止相對路徑。

---

## 📅 2026-08-25 交接紀錄
- 優化收工規則：整合互動式按鈕選單與自動跳版號 Tag 流程至 AGENTS.md。

---

## 📅 2026-08-16 交接紀錄（台積三合一單 + COA 雙重核對）
- 金鑰移至試算表「設定」分頁，支援多組 Google Vision + Gemini 金鑰輪替。
- 多模型瀑布流降級：Vision 失敗 → Gemini 3.6-flash → 3.1-flash-lite。
- 實作 API_Log 日誌紀錄分頁。
- 注意：USAGE_LIMIT（預設 900）必須填在試算表 B 欄。

---

## 📅 2026-08-03 交接紀錄（N系列 v1.9 APK）
- 修復料號首字 1 或 7 被誤判為批號格式錯誤。
- N-系列出貨核對-v1.9.apk 已編譯並備份至 Google Drive。
