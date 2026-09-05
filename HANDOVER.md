# 跨電腦交接日誌 (HANDOVER)

## 2026-09-05 收工交接 (正式上線發布：PWA 雙軌架構實施與 eshine-package 上線)
- **完成項目**：
  1. **全專案 PWA 雙軌架構標準化 (PWA Dual-Track Architecture)**：
     - 在 `AGENTS.md` 與中央大腦 `INSTRUCTIONS.md` 確立 Rule 7 (純 ASCII BAT) 與 Rule 8 (PWA 雙軌 `1_Web_網頁版` / `2_PWA_App版`) 開發規範。
     - 重構「倉庫常用包材管理」與「N系列BARCODE出貨核對」專案，拆分雙軌目錄並配齊 `manifest.json`、`sw.js`、高解析圖示 (`icons/`)、`run_server.py` 與 `一鍵部署到Cloudflare.bat`。
  2. **鴻勝包材管理系統 v13.5 (Eshine Package) 雲端正式上線**：
     - 整合即時 GAS Web App 後端與高質感藍灰 Bootstrap 5 介面。
     - 透過 Wrangler Direct Upload 成功部署至 Cloudflare Pages：**`https://eshine-package.pages.dev`**。
     - 具備離線快取防呆與三端 (Windows/Mac 電腦獨立視窗、Android 桌面圖示、iOS Safari 加入主畫面) PWA 獨立 App 安裝能力。
  3. **Git 倉庫健全性修復 (Submodule / Gitlink 清理)**：
     - 清除 Git 索引內殘留之 22 個無效 `160000` gitlink 孤立指標，徹底解決 Cloudflare 雲端 build clone 失敗問題。
  4. **全套圖文手冊產出與 Git 強制納管**：
     - 產出《鴻勝包材管理系統_操作手冊》與《Cloudflare_Pages_完整部署與疑難排解手冊》之 Word (.docx) 及 PDF (.pdf) 文件，並以 `git add -f` 強制納管。
- **遇到的問題與解決**：
  - **Windows CMD BAT 亂碼 (`嚜濃echo`)**：UTF-8 BOM 導致 CMD 報錯。解法：全面改為純 ASCII 3 行 BAT (`@echo off\npython run_server.py\npause`)，控制台繁體中文輸出全權由 Python 接管。
  - **瀏覽器本機中文亂碼 (`暾餃蝠ㄥ蝟餌紋`)**：HTML 與伺服器缺少 utf-8 編碼宣告。解法：注入 `<meta charset="UTF-8">` 並在伺服器回應標頭設定 `Content-Type: text/html; charset=utf-8`。
  - **Cloudflare Git Clone 報錯**：`fatal: No url found for submodule path in .gitmodules`。解法：使用 `git update-index --force-remove` 將所有 160000 虛擬指標從 Git 索引剔除。
  - **Cloudflare 免費方案佇列排隊**：雲端 Build 需排隊等容器。解法：改用 Direct Upload (Wrangler API Token)，3 秒直傳全球邊緣節點。

## 2026-09-04 深夜收工 (正式上線發布：線上地點代號回寫主機端功能)
- **完成項目**：
  1. **線上網頁端地點代號即時回寫主機電腦端**：
     - 在 `server.py` 實作 `/api/save_location` 與 `/api/delete_location` API 端點。
     - 線上同仁無論使用手機、平板或遠端瀏覽器新增地點時，系統自動將資料同步寫入電腦端 `地點代號對照表.xlsx`（包含三合一單網頁架機伺服器、三合一單自動產生器、勝一三合一單產生系統多端同步）。
     - 網頁端排程表格即時反應更新，免重新整理頁面；本機桌面版點擊「重新載入」亦可立即同步。
  2. **未知地點智慧點擊回寫導航 (Zero-Friction UX)**：
     - 表格排程遇到未建檔地點時，長代碼欄位呈現紅色指針按鈕樣式 `❌ 未知代號 (點此回寫新增)`。
     - 點擊後自動彈跳地點維護視窗並預填短地點代碼，同仁只需輸入長代號並點擊儲存，表格全列立即刷新。
  3. **UI 介面最佳化與按鈕收斂**：
     - 移除工具列多餘折行按鈕，將 `📍 地點代號維護 (回寫電腦端)` 統一整合至綠色連線狀態列右側，工具列恢復單行整齊排列。
  4. **全廠區 30 處地點對照碼鏡像整合**：
     - 整合並同步 12P、14P、15P、18P、AP、20P、22P 等 30 處完整對照表至全專案 Excel 檔案。
  5. **時間格式正規化防呆**：
     - 解決 SheetJS 將 Excel 純時間小數解析為 1899-12-30 導致小輸入框顯示 `SAT DEC 30` 之問題，前後端全面保證純 4 碼時間輸出（如 `0900`, `1400`, `1600`）。
- **遇到的問題與解決**：
  - **線上與電腦端對照表割裂**：線上人員無法登入主機手動開 Excel。解法：建立後台檔案安全寫入與多專案鏡像回寫機制。
  - **工具列折行不美觀**：多加按鈕導致第二行破版。解法：收斂整合至綠色連線狀態列右側，維持工具列清爽。
  - **Excel 小數時間字串化破版**：SheetJS cellDates 解析為 Date 物件在字串化時包含星期與日期。解法：封裝 `normalizeTimeStr` 函式精準提取純 4 碼時間。

## 2026-09-04 晚間交接事項 (正式上線發布：main + Tag)
- **完成項目**：
  1. **三合一單檔名規則更新（出貨日 + 槽號 + 廠別）**：
     - 原命名：2026.8.18. 18P3B台積電槽車barcode三合一單.xlsx
     - 新命名：2026.8.18. E44 18P3B台積電槽車barcode三合一單.xlsx
     - 本地桌面版 (main.py) 與 網頁版 (server.py) 全面同步支援。
  2. **單列生產履歷 Excel 獨立產生功能 (Chemical_Lorry)**：
     - 原檔命名後半段更新：在廠別前加入槽號，如 Chemical_Lorry_...勝一化工股份有限公司-0905 E44 15P5.xlsx。
     - 解決 ws.delete_rows() 處理 1897 列超大範本當機效能問題：改採全新工作表精準建構法 (uild_single_row_lorry_workbook)，在 1 秒內極速完成產出。
     - 視窗視角修復：移除 	opLeftCell='A7' 強制捲動偏移，確保打開 Excel 時從第 1 列至第 7 列完整顯示，表頭與排程一目了然。
     - 自動欄寬與高度最佳化：依據欄位字串長度與表頭長度自動計算最佳欄寬（21~35），文字不再被遮蔽或折行，第 6 列表頭高度擴大至 28.0。
  3. **UI 介面排版優化與報表勾選分離**：
     - 本地桌面版：工具列左側放置資料載入按鈕，右側放置表格列操作按鈕；獨立出「欲產生的報表勾選」區域，支援單獨或一鍵產出三合一單、運輸通知表、生產履歷 Excel。
     - 新增「📋 載入生產履歷 (Chemical_Lorry)」獨立按鈕與檔案路徑狀態顯示。
  4. **修復桌面端 UnboundLocalError 語法問題**：
     - 清除函式內部所有巢狀 import，將 os、
e、glob、json、csv 等標準函式庫全面提升至頂層，徹底解決點擊按鈕無反應問題。
  5. **正式合併至 main 並發布 Tag**：
     - 經測試驗證通過，將 eat/20260904 完整合併至 main，並升級發布新版本 Tag。
- **遇到的問題與解決**：
  - **Openpyxl 刪除列效能瓶頸**：範本含有全欄格式導致 max_column=16384，ws.delete_rows() 會極度消耗 CPU 卡死。解法：改用新工作表只複製前 30 欄及目標列資料，1 秒內生成完畢。
  - **Excel 打開視角遮蔽表頭**：因誤設 	opLeftCell='A7' 導致畫面捲動遮蔽第 1~6 列表頭。解法：保持預設 A1 視角並保留 A7 凍結窗格。
  - **欄位文字被切斷**：原欄寬為預設 13，導致 PM 日期與批號被遮擋。解法：動態計算字元長度並自動設定最佳欄寬。
  - **Tkinter UnboundLocalError**：函式中途放置 import os 導致變數作用域被鎖定為 local。解法：全域重構清除所有巢狀 import。

## 2026-09-04 日間交接事項 (進度：三合一單自動產生器與教材系統)
- **完成項目**：
  1. 取得勝一教育訓練 PPT，使用 win32com 完成範本套用轉換。
  2. 桌面版 Excel 讀取優化，支援讀取全工作表資料。
  3. 匯入範圍預覽對話框，多欄位 Treeview 瀏覽。
  4. 批號自動解析槽號、長代碼對照與鍵盤上下左右導航。
