# ACT 動態生產排程與進耗存整合系統 (Cloudflare 邊緣雲端版)

本系統為 **ACT 專用動態生產排程、槽車出車與 30 日進耗存推算系統**。
架構採用 **Cloudflare Pages 邊緣前端 + Google 試算表（Google Apps Script）雲端資料庫** 雙核心混合架構。

## 🌟 核心特點
1. **多產品通用配置 (Profile 切換器)**：支援多產品切換（如 ACT、IPA、新產品），各產品可獨立配置槽桶與容量，不需為新產品重寫系統。
2. **動態槽桶管理 (可自訂增減)**：原料區與成品區槽桶名稱與數量支援自由「➕ 新增 / ➖ 刪除」，不再寫死槽號，通用於各產線槽桶配置。
3. **秒級載入 (0.2 秒)**：託管於全球 Cloudflare 邊緣節點，免除 Google Apps Script 的載入轉圈等待。
4. **乾淨 UI**：全無 Google「*這個應用程式是由 Google Apps Script 使用者建立*」頂部警告橫條。
5. **資料庫留在 Google 試算表**：全廠人員依然可在熟悉的 Google Sheets (`ACT_DataStore` / `ACT_ArchiveStore`) 即時查看與備份資料。
6. **小數點第一位（0.1 T）精確計算**：排產流速、首日次班出料折算、末日自動補齊尾數。
7. **槽車排程動態聯動**：填寫順序自動排車；清空順序自動 100% 清空排程。

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
