# ACT 動態生產排程與進耗存整合系統 (Cloudflare 邊緣雲端版)

本系統為 **ACT 專用動態生產排程、槽車出車與 30 日進耗存推算系統**。
架構採用 **Cloudflare Pages 邊緣前端 + Google 試算表（Google Apps Script）雲端資料庫** 雙核心混合架構。

## 🌟 核心特點
1. **多產品通用配置 (Profile 切換器)**：支援多產品切換（如 ACT、多儲槽成品 TK623/689/692、新產品），各產品可獨立配置槽桶與容量，不需為新產品重寫系統。
2. **儲槽容量上限與總滿位自動換算**：各成品儲槽清楚標註容量上限（如 `TK623 (125T)`），頂部即時顯示「總容量滿位：儲槽 X 噸 + 槽車 Y 噸 = 總滿位 Z 噸」。
3. **槽車存量與其他存量 100% 納入期初總成品計算**：打入槽車存量（如 36T）與其他存量即時加總至「總計期初成品」，並作為 30 日進耗存推演第 1 天起算庫存。
4. **雙階儲存容量預警**：成品結存推估超出實體儲槽時顯示黃底警示（提醒調用槽車存放），超出儲槽加槽車總滿位時顯示紅底高亮警示（防止全廠飽和溢流）。
5. **動態槽桶管理 (可自訂增減)**：原料區與成品區槽桶名稱與數量支援自由「➕ 新增 / ➖ 刪除」，不再寫死槽號，通用於各產線槽桶配置。
6. **秒級載入 (0.2 秒)**：託管於全球 Cloudflare 邊緣節點，免除 Google Apps Script 的載入轉圈等待。
7. **資料庫留在 Google 試算表**：全廠人員依然可在熟悉的 Google Sheets (`ACT_DataStore` / `ACT_ArchiveStore`) 即時查看與備份資料。
8. **小數點第一位（0.1 T）精確計算**：排產流速、首日次班出料折算、末日自動補齊尾數。
9. **槽車排程動態聯動**：填寫順序自動排車；清空順序自動 100% 清空排程。

## 📂 完整檔案結構
```
C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統\
├── public\
│   └── index.html               # Cloudflare Pages 前端完整 SPA 網頁
├── Code.gs                      # 貼入 Google Apps Script 的 API 後端
├── 一鍵部署至Cloudflare.bat      # 一鍵發布至 https://act-planner-pwa.pages.dev
├── setup_env.ps1                # 環境檢查腳本
├── SKILL.md                     # AI 維護說明書
└── README.md                    # 本說明書
```

## 🚀 跨電腦啟動與部署步驟
1. 雙擊執行 `一鍵部署至Cloudflare.bat`。
2. 系統自動執行 `wrangler pages deploy` 將最新代碼部署至 Cloudflare。
3. 部署完成後自動開啟 `https://act-planner-pwa.pages.dev`。
