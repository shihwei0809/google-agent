# 跨電腦交接日誌 (HANDOVER)

## 今日進度與交接事項 (2026-10-30 ACT/EGUPS動態生產排程 v2.0 升級與系統問題診斷修復)
* **ACT動態生產排程與進耗存整合系統 (`C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統\`) 升級至 `v2.0` 並部署至 Cloudflare Pages (`https://act-planner-pwa.pages.dev`):**
  - **根治試算表自動同步回傳時區 `+8 小時` 跳日 Bug (`formatDateTimeLocal`)**:
    1. **根本原因**: Google Sheets 將 `2026-11-16T16:00` 辨識為日期型態後，透過 GAS `JSON.stringify` 回傳時會自動轉為 `2026-11-16T16:00:00.000Z`（多了尾部 `Z`）。前端 `formatDateTimeLocal` 原本在遇到 `Z` 時會交給 `new Date(val)` 解析，導致瀏覽器自動加上台灣時區 `+8 小時`，把 `2026/11/16 16:00` 推成 `2026/11/17 00:00`，進而使排程起始日往後跳一天、`11/16` 當日 `90T` 進貨被擠出排程（總進貨由 `720T` 變成 `630T`）。
    2. **處置方案**: 修改 `formatDateTimeLocal(val)`，無論字串是否帶有 `.000Z`，一律優先以正規表示式 `^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})` 直接截取年月日與時分，徹底杜絕時區偏移。
  - **歷史存檔區 (`ACT_ArchiveStore`) 跨裝置完整同步 (`fetchCloudArchives`)**:
    1. 新增 `fetchCloudArchives(targetProduct)` 並於啟動、切換產品及讀取雲端時自動呼叫 GAS `action: "get_archives"`，將試算表 `ACT_ArchiveStore` 內所有歷史存檔（共 4 筆 EGUPS 紀錄）完整合併回前端下拉選單。
    2. 點擊「讀取」載入歷史存檔後，自動觸發 `saveToCloud(true)` 將該歷史排程同步寫入雲端試算表，確保多人查看一致。
  - **多人協作背景定時自動更新 (`silentAutoRefreshFromCloud`)**:
    1. 新增每 60 秒定時輪詢、視窗重新取得焦點 (`window.focus`) 與分頁切換回來 (`visibilitychange`) 時自動靜默拉取雲端最新排程。
    2. 內建 `isUserEditingInput()` 防護機制：當人員正在輸入框打字或尚有未上傳的變更 (`autoSyncTimer` / `isSavingToCloud`) 時自動跳過更新，絕不中斷打字。

* **Antigravity 編輯器 Git 自動掃描卡死 100% CPU 徹底根治:**
  - **根本原因**: Antigravity (VS Code 底層) 預設開啟 Git 背景自動監視，在工作區包含數十個歷史 .git 專案時，會瞬間並行發動數十個 git.exe 執行全盤掃描；同時觸發公司端趨勢防毒 (Trend Micro) 檔案攔截檢查，導致進程鎖死互咬，CPU 瞬間衝破 100%。
  - **處置方案**: 於 C:\Users\C606-PC\AppData\Roaming\Antigravity\User\settings.json 寫入 git.enabled: false 與關閉深度掃描。編輯器背景徹底停止自動掃描，而終端機、開工收工腳本與 AI 的 Git 功能完全正常不受任何影響。

* **回收液入料記錄系統 Cloudflare Pages 中華電信誤判阻擋排除 (雙軌入口架構):**
  - **根本原因**: 中華電信 HiNet 企業固網 (SOC) 將 
ecycle-feed-records.pages.dev 網址誤判為 Category: phishing 釣魚網站。桌機因加入公司網域 (eshineac.com.tw)，走內網 DNS，HTTPS 請求發出時在 SNI 階段被 HiNet 防火牆強制中斷 (ERR_CONNECTION_CLOSED / ERR_QUIC_PROTOCOL_ERROR)。手機因連 WiFi 時走系統預設的加密 DNS (DoH/ECH) 未外洩網域名稱，故手機連線正常。
  - **公司資安限制**: 桌機之 Chrome 與 Edge 瀏覽器因受公司 AD 網域原則控管，安全 DNS (DoH) 選項皆呈鎖定狀態，無法於本機手動切換。
  - **雙軌入口架構 (免重裝公務機)**:
    1. 原網址 https://recycle-feed-records.pages.dev **完整保留不動**，確保現場所有已安裝 PWA 之公務機手機完全不受影響、不需重新安裝。
    2. 透過 Cloudflare Pages 另外部署專案 
ecycle-portal (https://recycle-portal.pages.dev)，綁定同一 D1 資料庫 (egups-db)。
    3. 桌機連線至新入口實測回傳 HTTP 200 秒開，且能即時同步讀取今日現場入料之最新資料。

## 今日進度與交接事項 (2026-10-29 小包系統報表產生器_勝一專用版 重大功能升級：COA/PR檔名與資料夾全面切換為到貨日、品名獨立分群產出、COA內部批號嚴格核對、超量折疊與排程反選)
* **小包系統報表產生_勝一 (`c:\GOOGLE ANGET\小包系統報表產生_勝一\`):**
  - **COA 與生產履歷 (PR) 檔名尾部日期全面改為「到貨日」**:
    1. 修正原預設出貨日邏輯，全面依勝一業務規範將檔名尾部切換為「到貨日 (arr_date) 8 碼」（若無到貨日才自動 fallback 出貨日）。
    2. COA 檔名規格：`COA_L2C9172_A515_CPN_VISERA_20261030.CSV`
    3. PR 檔名規格：`PR_L2C9172_75970680_VISERA_Shiny20261030.xlsx`
  - **資料夾全面採用「到貨日」並分品名獨立產出 (`N系小包報表輸出_[品名]_[到貨日]`)**:
    1. 產出主資料夾捨棄出貨日，全面改依「到貨日」與「品名」分群產出（例如 `N系小包報表輸出_CPN_20261030\`、`N系小包報表輸出_PMAUPS_20261030\`）。
    2. 內建 `get_canonical_prod_name` 智慧標準化品名代碼（如 `CPNE4`/`A515` ➔ `CPN`、`PMAUPS` ➔ `PMAUPS`、`PMAHQ(R)` ➔ `PMAHQ`、`SEP73E4` ➔ `SEP73E4`）。
    3. 徹底解決不同品名報表混雜在一起之問題，COA、PR、三合一單與運輸通知表 100% 依品名與到貨日自動歸位。
  - **COA 與生產履歷 (PR) 100% 統一同廠區資料夾**:
    1. 根治先前半段用清理簡稱（`VISERA`）、後半段用原始中文（`台積電VisEra廠`）導致產出被拆為兩個資料夾的缺陷。
    2. 建立統一函式 `get_report_loc_folder`，所有單據皆經標準化路徑計算，無論模式 1 或模式 2 皆同廠同資料夾。
  - **COA 載入結果視窗升級為「A+B 旗艦組合版」（捲動表格 + 分類 Tab + 搜尋與一鍵複製）**:
    1. 徹底替換原生無捲軸的 `messagebox.showinfo`，新增獨立 `CoaResultDialog` 視窗（固定 880×520，居中彈出，絕不撐爆螢幕）。
    2. **方案 B 精華（分類篩選 Tab）**：頂部具備 `[全部 (X)]`、`[✅ 成功核對 (Y)]`、`[⚠️ 未配對排程 (Z)]` 一鍵切換檢視。
    3. **方案 A 精華（完整捲動表格與複製）**：
       - 包含欄位：`[狀態]` | `[#]` | `[COA 來源檔名]` | `[內部 RawLotId 批號]` | `[排程配對批號]` | `[廠區簡稱]` | `[核對說明]`。
       - 支援即時關鍵字搜尋過濾。
       - 具備 `[📋 一鍵複製表格清單]` 按鈕，點擊可直接複製整齊表格貼入 Excel 或通訊軟體備查。
       - 支援鍵盤 Esc / Enter 快速關閉。
  - **COA 內部批號嚴格核對（100% 只認 RawLotId，絕不依檔名猜測）**:
    1. COA 是品保核心文件，徹底移除任何檔名回退比對邏輯。
    2. 嚴格解析來源檔案內部之 `RawLotId` 欄位（支援多種編碼與大小寫），與勾選排程客戶批號完全相符才允許載入與產出。
  - **生產履歷 (PR) 多模版精確比對（Longest Match First）與 Tank No. 固定保護**:
    1. 實作多層精準匹配演算法，避免 `PMAUPS` 與 `PMAHQ(R)` 互搶覆蓋。
    2. Tank No. 固定於模版，系統寫入排程資料時保護原值不予覆蓋。
  - **排程匯入/主畫面全選、全部取消、反選功能與 PO 貼上防呆**:
    1. `ImportRangeDialog` 新增反選、全選、全部取消按鈕；主畫面表頭與工具列新增反選快捷功能。
    2. PO 欄位支援多行貼上並避免污染批號變數，產出核對嚴格鎖定「客戶批號 (Lot No)」為 10 碼。
  - **修改範圍保證**:
    1. 100% 保持 `n系統報表產生` 為乾淨狀態，所有改動 100% 侷限在 `小包系統報表產生_勝一\main.py`。

## 歷史進度存檔 (2026-10-28 小包系統報表產生器_勝一專用版 重構12欄位、台積28廠別x5品名對照表、簡稱欄位核對與嚴格雙條件代入料號)
* **小包系統報表產生_勝一 (c:\GOOGLE ANGET\小包系統報表產生_勝一\):**
  - **專案正名與更新腳本對齊**:
    1. 將原 `n系統報表產生_勝一` 正名為 `小包系統報表產生_勝一`。
    2. 更新 `一鍵更新系統程式.bat` 之 URL 編碼下載路徑（`小包系統報表產生_勝一/main.py`）。
    3. 同步修訂 `README.md`、`SKILL.md`、`setup_env.ps1` 與專案交接日誌。
  - **主畫面表格與預覽視窗全面重構為勝一排程 12 核心欄位 + 簡稱核對**:
    1. 表格欄位嚴格對齊勝一排程：`[產生]` | `[項次]` | `[指送地 (地點)]` | `[簡稱]` | `[品名]` | `[規格]` | `[預計出貨日 📅]` | `[預計到貨日 📅]` | `[到貨時間]` | `[單重]` | `[件數]` | `[出貨數量]` | `[車牌]` | `[原料批號]` | `[客戶批號 (Lot No)]` | `[清空單列]`。
    2. 新增 `[簡稱]` 欄位居中橘色粗體顯示，指送地輸入或排程匯入時自動帶出代碼（如 `F20P1`、`FB30`、`7F3E`），人員可直覺核對與手動修改。
    3. 主視窗尺寸優化為 1360x840，預覽對話框同步對齊呈現。
  - **台積小包材地點代號對照表全面升級 (28 廠別 × 5 品名)**:
    1. 產生標準 `台積小包材地點代號對照表.xlsx`，共 141 列，A 欄為指送地完整中英文名稱、B 欄為簡稱、C 欄為品名（`PMAUPS`、`CPNE4`、`SEP73E4`、`PMAHQ`、`PMAHQ(R)`）、D 欄為工廠地點、E/F 欄為預設料號。
    2. 支援模糊檔名相容載入：目錄下只要檔名包含「地點代號對照表」或「代號對照表」皆可自動識別載入，狀態列動態顯示目前使用之檔名。
  - **料號嚴格雙條件精準核對（無匹配一律留空）**:
    1. 嚴格貫徹「廠區地點」與「品名」雙條件核對，完全移除單依地點查詢的 fallback 機制，避免不同產品誤代料號。
    2. 若僅填地點無品名、或該品名尚未設定料號，料號一律直接留空，後續人員手工補登或等官方模版確認。
  - **徹底修復指送地誤填批號與變數宣告作用域問題**:
    1. 移除舊版寫死 fallback `batch_col = 2`，批號英數格式檢查排除中文雜訊，未排批號之預排單據精準留空。
    2. 解決 `load_excel` 中 `cust_val` 變數作用域錯誤。
  - **報表寫入鎖定保護**:
    1. COA 與 Chemical_Lorry 生產履歷寫入邏輯嚴格維持不動，待人員提供正式範本再行對應。

## 今日進度與交接事項 (2026-10-27)
* **三合一單自動產生器 (c:\GOOGLE ANGET\三合一單自動產生器\):**
  - **版本號全面統一推進至 v2.2.4 (2026/10/27更新)**:
    1. **版本不一致根治**: 修正先前 main.py 標記為 2.2.3 但安裝腳本保留 2.2.2 的衝突問題，全面將 main.py 視窗標題、installer.iss 與 splash.png 統一升級至 v2.2.4。
    2. **核心純粹性保障**: 全流程嚴格僅更新版本號標籤與啟動畫布，未更動任何 Excel 產表、OCR、條碼或列印業務核心邏輯。
  - **PyInstaller 免安裝版重新封裝與 Splash 啟動優化**:
    1. **啟動白框/tk視窗根除**: 針對 PyInstaller 的 text_pos 在 Windows 繁中環境下因 Tcl 字型名稱或 UTF-8 中文未轉義而拋出例外導致殘留白色羽毛方塊的問題，改為直接將版本字樣繪製於 splash.png 高解析深色卡片上，spec 設定 text_pos=None，達成秒開零破圖。
    2. **產出免安裝版**: 成功打包生成最新 dist\三合一單自動產生器-免安裝版.exe。
  - **Inno Setup 標準安裝檔重新編譯**:
    1. 透過 Inno Setup 6.7.3 成功編譯生成最新安裝程式 Output\三合一單自動產生器_Setup_v2.2.4.exe。
    2. 自動配置桌面捷徑、程式集、反安裝程式與靜態依賴檔案（Excel範本與splash等）。

## 今日進度與交接事項 (2026-10-27 建立「N系列報表輸出系統 (勝一專用版)」獨立專案)
* **N系列報表輸出系統 (勝一專用版) (`c:\GOOGLE ANGET\n系統報表產生_勝一\`):**
  - **專案隔離獨立分流**: 自原鴻勝版完整複製並建立獨立專案目錄，版本號推進為 `v1.0.0 (勝一專用版 2026/10/27)`，視窗標題自帶專用識別。
  - **一鍵更新精靈獨立定向**: `一鍵更新系統程式.bat` 之雲端直接下載路徑更新為 `n系統報表產生_勝一/main.py`，與鴻勝版本更新徹底分流。
  - **標準專案四件套建置**: 補齊 `README.md`、`SKILL.md`、`setup_env.ps1` 與專案交接日誌，啟動與相依套件檢測腳本一併配置完成。
  - **地點與料號對照確認**: 經確認勝一之「地點與料號對照」與鴻勝完全相同，共用現行對照表即可；後續等候勝一人員提供「排程 Excel 範本」與「COA/生產履歷輸出格式」再行調整對應程式碼。

## 前次進度與交接事項 (2026-10-26 回收液入料系統手動完成雙向對齊修復、Google試算表全新自訂欄位順序支援)
* **回收液入料記錄 App (`recycle-feed-records.pages.dev` / `3_Cloudflare_D1版`):**
  - **Google 試算表強制完成 (completed) 狀態自動回寫 D1**:
    1. **問題排查**: 使用者在 Google Sheets 手動將 10/22 紀錄強制改為 completed，但 Cloudflare D1 依然停留為 pending，導致 App 前端兩邊取聯集時依然顯示待入料。
    2. **雙向自動對齊**: 前端更新為 16-D1，載入待入料時以 Google Sheets query 狀態為權威，若 Sheets 已完成則自動剔除並發送背景請求回寫修復 Cloudflare D1，已將 10/22 幽靈待入料全數清除對齊。
  - **Google 試算表欄位順序客製化升級**:
    1. **欄位重構**: 將 入料前時間 (E)、入料後時間 (F)、歷時(分) (G) 前移緊接在 狀態 (D) 之後，照片 URL (H, I, J) 後移至最後三欄。
    2. **GAS 後端更新**: 更新 Code.gs 的 setup()、doGet(action=query/pending)、handleBeforeFeed()、handleCompleteFeed() 與 handleAfterFeed()，確保對調欄位後讀寫對應精準無誤。
    3. **Cloudflare D1 驗證**: 確認 D1 為具名 Column 欄位架構，完全不受 Google 試算表格子順序異動之影響。

  - **全系統 API KEY 盤點與 Cloudflare 雲端加密環境變數升級**:
    1. **全面清查**: 盤點系統內全部 9 個 .env 檔案，確認核心業務專案（回收液、ACT、IPA、穿透中心）之敏感金鑰 100% 留存於伺服器端。
    2. **教育訓練平台金鑰抽離**: 將 unctions/api/ (chat.js, convert_sop.js, generate_image.js) 寫死的明文金鑰陣列完全抽離，改由 Cloudflare 後台 env.GEMINI_API_KEY 加密機密 (secret_text) 注入，支援多組逗號分隔自動輪替。
    3. **Cloudflare 雲端教材一鍵備份工具落地**: 建立 一鍵備份雲端教材.py 與 一鍵備份雲端教材.bat，可自動調用 API 將 Cloudflare R2/D1 中的全數 15 份教材 Markdown 檔案秒級下載並備份至本機 雲端教材備份 目錄。

## 前次進度與交接事項 (2026-10-25 HTTPS 遠端網頁穿透中心黑邊坐標偏差逆推修復、單雙擊防抖分離與雙擊開檔時序優化、免安裝 EXE 重新封裝、Cloudflare RDP 原生穿透腳本建置)
* **HTTPS 遠端網頁穿透中心 (C:\GOOGLE ANGET\HTTPS遠端網頁穿透中心\):**
  - **遠端滑鼠點擊與雙擊開檔深度修復 (main.py, static/index.html)**:
    1. **消除 object-contain 黑邊坐標偏差**: 針對不同長寬比螢幕產生的上下/左右黑邊（Letterbox），實作幾何比例逆推扣除邊距，徹底根除滑鼠點擊坐標平移偏差，實現 100% 像素精準對齊。
    2. **單擊/雙擊防抖分離 (Debounce Separation)**: 前端加入 180ms 單擊防抖機制。當使用者快速雙擊時，自動攔截取消單擊請求，避免多次單擊被網路延遲拆散而誤入 Windows 檔案重新命名模式。
    3. **Windows 雙擊開檔黃金時序**: 後端 handle_screen_mouse 嚴格遵循 Windows 雙擊時序（Click 1 -> 70ms 最適間隔 -> Click 2），並徹底移除先前干擾雙擊的 Alt 鍵連動，確保 Windows 檔案總管 100% 穩定觸發開啟檔案與資料夾。
    4. **免安裝單一執行檔重新打包**: 使用 PyInstaller 6.21.0 重新編譯封裝完成，產出最新版 dist\HTTPS遠端穿透中心-免安裝版.exe。
* **Cloudflare RDP 原生遠端桌面穿透 (C:\GOOGLE ANGET\):**
  - **一鍵啟動腳本建置 (一鍵啟動RDP穿透(微軟遠端桌面).bat)**:
    1. 利用本機現有 cloudflared.exe 自動建立 RDP 3389 穿透隧道，偽裝為標準 443 HTTPS 網頁流量，100% 穿透企業防火牆。
    2. 自動抓取並顯示筆電端連線指令，且自動產生 筆電端一鍵連線.bat 與 最新RDP穿透網址.txt，連線即可享受 60FPS 原生桌面、跨機複製貼上檔案與筆電磁碟直接掛載。

## 前次進度與交接事項 (2026-10-24 NoType AI 語音輸入法 Gemini/Groq 極速混用與免安裝打包、HTTPS 遠端穿透中心個人帳號設定與免安裝打包、三合一單自動產生器免安裝打包與啟動畫面優化)
* **NoType AI 語音輸入法 (`C:\notype-master\`):**
  - **Google Gemini 一鍵轉錄＋潤飾引擎與自動降級/混用機制 (`src/api/gemini.js`, `src/shortcut.js`, `src/api/llm.js`)**:
    1. 支援 Google AI Studio 新版 `AQ.` 與 `AIza` 金鑰格式（透過 `x-goog-api-key` Header）。
    2. 實作 `transcribeAndPolishWithGemini` 單次請求同步完成語音轉文字與潤飾，省去二次 API 往返時間；並將 `src/typer.js` 剪貼簿貼上延遲由 550ms 縮短至 170ms。
    3. 針對免費版配額限制（`gemini-3.8-flash` / `3.6-flash` 僅 20 RPD 且超額會無限排隊），加入 `AbortController` 2.0s~3.5s 強制超時中斷與跨日自動重置黑名單 (`blacklistDate`)，優先鎖定高配額極速模型 `gemini-3.1-flash-lite`（500 RPD，約 1.9 秒完成）。
    4. 支援 Gemini ⇄ Groq (`whisper-large-v3-turbo` / `llama-3.3-70b-versatile`) 雙引擎自動備援，當單一平台配額耗盡時自動無縫切換。
    5. 修復 `start.bat` 中文亂碼 (`chcp 65001`) 與舊背景程序搶佔 `Alt+Space` 快捷鍵問題，並打包產出零金鑰殘留之免安裝單一執行檔 `dist\NoType-Portable-1.0.0.exe`。
* **HTTPS 遠端網頁穿透中心 (`C:\GOOGLE ANGET\HTTPS遠端網頁穿透中心\`):**
  - **遠端畫面黑框消除與雙軌文字注入修復 (main.py, static/index.html)**:
    1. **消除 Chrome/Edge/Terminal 畫面黑框**: 未鎖定狀態下全面使用原生 ImageGrab，徹底消除先前視窗被 PrintWindow 捕捉為黑方塊的問題，畫面清晰還原。
    2. **雙軌文字注入 (64-bit 原生剪貼簿 + SendInput UNICODE)**: 支援 Win32 64-bit 原生剪貼簿注入搭配 Ctrl+V，100% 支援任意中英文長字串、標點符號與多行文字；並以 SendInput UNICODE 作為第二道防護。
    3. **點擊強制奪取焦點 (Alt Key Trick)**: 點擊遠端視窗時自動透過 Win32 模擬 Alt 鍵繞過 Windows 前景鎖定限制，確保滑鼠點擊立即啟動該視窗並接受鍵盤文字輸入。
  - **支援個人 Google 帳號登入設定與單一免安裝 `.exe` 封裝 (`main.py`, `static/index.html`)**:
    1. 新增 `/api/account/info` 與 `/api/account/setup` 端點，並在前端登入畫面（本機直連時）與系統頂部導覽列新增「👤 帳號設定」彈窗 (`#account-modal`)。
    2. 任何使用者皆可自行輸入個人的 Google 帳號 (Email)、自訂專屬管理密碼，並一鍵重設專屬 2FA QR Code 綁定自己的手機 Google Authenticator，完全不共用開發者帳號。
    3. 封裝為免安裝單一執行檔 `dist\HTTPS遠端穿透中心-免安裝版.exe`（自動排除 `security_config.json` 確保無個人金鑰外洩）。
* **三合一單自動產生器 (`C:\GOOGLE ANGET\三合一單自動產生器\`):**
  - **免安裝 `.exe` 封裝、對照表防覆蓋與 0.1 秒極速啟動提示畫面 (`main.py`, `splash.png`)**:
    1. 修正啟動時提取預設資源檔邏輯：只要執行目錄下存在任何檔名包含 `地點代號對照` 的 `.xlsx` 檔案（例如使用者自訂之 `地點代號對照表--20261025.xlsx`），就絕不再解壓縮產生預設的 `地點代號對照表.xlsx`，徹底解決新舊檔案並存誤讀問題。
    2. 整合 PyInstaller `--splash "splash.png"` 原生啟動畫面與 `pyi_splash.close()` + 視窗置頂 (`-topmost`)，雙擊 `dist\三合一單自動產生器-免安裝版.exe` 0.1 秒內立即彈出「🚀 系統啟動中 — 三合一單自動產生器」提示框，消除單一執行檔解壓縮期間無反應的困惑。
    3. **實作方案 B（GitHub 雲端熱更新 & 離線四層防呆保底機制）**：免安裝 `.exe` 啟動時自動於 2.5 秒內連向 GitHub (`shihwei0809/google-agent`) 拉取最新 `main.py`（與 `static/index.html`）並快取於 `.cloud_cache/` 熱載入執行；若無網路、GitHub 搬遷或驗證失敗，自動無縫退回外部 `main.py`、上次快取或 `.exe` 內建版本，確保永不當機且往後更新程式碼免重新封裝 `.exe`。

## 前次進度與交接事項 (2026-10-23 Google Colab 影片工作流部署、原創角色「小偉」全套資產庫建立、工廠裝卸料員工教學分鏡試映、AI 克隆聲音網站串接 Colab 黃金克隆母帶、收工規則修正)
* **GoogleColab影片 (`c:/GOOGLE ANGET/GoogleColab影片/`):**
  - **三師爸 Colab + MiniMax H3 雲端影片工作流部署與 Windows 修補**:
    1. 完整拉取並更新 `shanshiba-workflow-colab` 至最新提交，安裝 `google-colab-cli` (v0.7.4) 並執行 `cloud/colab_cli_windows_patch.py` 修復 Windows `termios` 相容性問題。
    2. 從直播串流擷取並留存 8 張 1080p 高清關鍵架構圖與角色資產結構表至 `直播圖表與角色資產參考/`（含 `01_兩種雲端跑法比較_Colab_H3_vs_Kie_Seedance.jpg`、`02_角色資產資料夾結構表.jpg` 等）。
  - **原創主角「小偉 (43歲、清爽旁分、無眼鏡、寫實風、沉穩男聲)」完整角色資產庫 (`pipeline/xiaowei_project/`)**:
    1. **雙造型全套三表 (`角色資產/小偉_正式版/` 與 `角色資產/小偉_休閒版/`)**: 鎖定同一張五官與清爽旁分短黑髮（不戴眼鏡），生成 `01_定妝照.png`（全身＋正面近照＋3/4側臉）、`02_轉面圖.png`（正/側/背/3/4 四視圖）、`03_表情表.png`（6 格演技表情），並合成 `角色資產總覽_小偉_正式版.jpg` 與 `角色資產總覽_小偉_休閒版.jpg`。
    2. **工廠現場裝卸料員工教學專案 (`pipeline/xiaowei_project/film.json`)**:
       - 生成台灣現代工廠裝卸貨月台與棧板暫存區 16:9 空場景母版 (`scenes/scene_01_loading_dock.png`)。
       - 合成 S01~S03 三鏡教學無字首幀 (`frames/s01.png`~`s03.png`) 與含字幕試映幀 (`s01_preview.png`~`s03_preview.png`)。
       - 產出 43 歲沉穩台灣男聲參考音 (`voices/ref_xiaowei.wav`) 與三鏡教學配音，並合成 23 秒試映影片 `讀本試映_小偉_工廠裝卸料教學.mp4`。
* **AI 克隆聲音網站串接 Colab 黃金克隆母帶 (`第三類_AI代理與指南企劃/AI 克隆聲音/app.py` & `教育訓練教材/ai-voice-cloner-guide/app.py`):**
  - **自動裁切 11 秒黃金母帶 (`build_colab_master_wav` & `sync_voice_to_colab_projects`)**:
    1. 網頁錄音儲存時，自動去除頭尾空白呼吸聲、正規化音量、裁切為 Colab (MiniMax H3 / BreezyVoice / VoxCPM2) 最佳的 11 秒黃金長度（含結尾 0.15 秒淡出防爆音）。
    2. 自動同步至 `GoogleColab影片/voices_master/` 與 `pipeline/xiaowei_project/voices/` 角色資產庫。
  - **網頁新增「☁️ Google Colab 黃金克隆母帶轉換 & 雲端 GPU 極速合成」面板**:
    1. 支援將本機既有錄音一鍵轉為 Colab 黃金克隆母帶。
    2. 支援直接選擇 `VoxCPM2 (48kHz)` 或 `BreezyVoice (台灣腔)` 引擎，透過 `colab_h3.py` 送上 Colab GPU 克隆新台詞並自動下載回本機。
* **中央大腦 (`%USERPROFILE%/.ai/INSTRUCTIONS.md`) 收工規範修正**:
  - 修正第 4 條收工規則：取消每次收工強制彈窗詢問主支/分支，**預設一律直接收工同步至 `main` 主支**；僅在使用者主動指定「有問題先存分支」時才推至開發分支。

## 前次進度與交接事項 (2026-10-22 QC 系統 PWA 離線作業模式實裝、指定日期清除排程功能、IndexedDB 本地暫存與自動連線同步、v3.0.5~v3.1.1 升級)
* **QC-系統客製化電子化工廠 (Cloudflare D1 版 / PWA):**
  - **T100 槽車排程「指定日期清除」精準管理 (v3.1.1)**:
    1. **可自選日期清除**: 點擊「🗑️ 清除排程 (選日期/全部)」開啟專用清理彈窗，系統自動統計並列出目前現存排程的所有日期與各日筆數（例如 2026-10-22 — 共 14 筆排程），並支援自訂日期。
    2. **安全防呆、避免誤刪全表**: 人員可選擇「僅清除選定日期排程」，後端 D1 資料庫與本機快取將只刪除該日期的排程，其餘日期的歷史排程完整保留。
    3. **後端 API 增強**: `functions/api/index.js` 的 `clearOrders` 擴充支援 `date` 參數，若有指定日期則執行 `DELETE FROM ... WHERE date = ? OR targetDate = ?`；若傳入 `ALL` 才進行整表清空。
    4. **Service Worker 版號升級**: 升級至 `qc-kanban-v3.1.1-offline`，線上環境已同步發布至 `qc-samples.pages.dev`。
  - **PWA 全功能離線模式 (Offline-First Architecture)**:
    1. **離線排程讀取**: 只要在辦公室有網路時開啟過一次，雲端最新 T100 排程自動快取至 `localStorage`。人員出發至現場或弱網槽區，完全斷網也能 0 秒秒開看板、完整讀取進出貨排程選單。
    2. **離線送樣與判定暫存佇列 (IndexedDB `QCOfflineDB`)**: 斷網時人員可正常執行「提交送樣」、「判定放行」、「退回重送」，系統自動轉入本地暫存佇列，看板介面即時呈現，絕不報錯中斷。
    3. **連線恢復自動同步 (Auto Sync)**: 偵測到連線恢復時（`online` 事件或定時每 30 秒），自動將所有暫存的送樣、判定資料依序推送回 Cloudflare D1，並彈窗提示同步成功筆數。
    4. **離線狀態橫幅提示**: 斷網時頂部自動浮現醒目紅色警報橫幅 (`#offlineBanner`)，明確提示目前暫存筆數。
    5. **Excel 解析完全離線化**: 將 SheetJS (`xlsx.full.min.js`) 直接內建打包並加入 `sw.js` 快取，徹底根除先前仰賴外部 CDN 造成的讀取逾時或視窗卡死問題。
  - **移除定期背景輪詢與按鈕計數即時歸零修復 (v3.0.5)**:
    1. **移除定期背景輪詢 (消除操作跳動干擾)**: 停用 `window.onload` 中的 `setInterval(load, 30000)` 與 `setInterval(render, 60000)`，改為靜默或依事件驅動更新。
    2. **Service Worker (sw.js) 快取判定漏洞修復**: 確保 `/api` 與 `/api/orders` 請求直通邊緣後端而絕不走快取。
    3. **API 請求防快取**: `loadOrdersFromCloud` 新增動態時間戳參數 `_t=${Date.now()}` 並設定 `cache: "no-store"`。
    4. **即時清空徽章狀態**: 當雲端回傳空陣列 `[]` 時，強制調用 `updateT100ButtonCounts()` 將過濾按鈕上的徽章數量即時歸零並更新畫面。
    5. **前端管理測試箱增強**: 新增「🗑️ 清空所有排程 (本機+雲端)」功能與「🔄 重新整理排程」按鈕，方便隨時校準排程。
    6. **版本升級與正式發布**: 全域版本號升級至 `v3.0.5` (`2ed39b3`) 並部署至 Cloudflare Pages (`qc-samples.pages.dev`)。

* **避坑指南 (Cross-Device Pitfalls):**
  - **PWA Service Worker 快取 API 陷阱**: PWA 快取策略若未嚴格過濾 `/api/*`，會導致後端資料庫即使已被清空，瀏覽器仍從 CacheStorage 撈出舊 JSON 回應，造成 UI 狀態與雲端資料不一致。

## 前次進度與交接事項 (2026-10-21 槽車與物流商評鑑稽核系統建立、雲端硬碟快照滾動封存機制修復、ACT動態排程槽車排序功能增強)
* **槽車運輸與物流外包商評鑑稽核體系 (資材實戰專用版):**
  - **稽核標準建立**: 依據最新稽核評鑑項目，精準梳理「第一項：品質系統 (1.1~1.7)」、「第三項：溝通和訓練 (3.1~3.3)」、「第四項：運輸安全 (4.1~4.10)」，共計 20 項細項指標。
  - **資材現場查核要點與佐證單據庫**:
    1. 實證查核：明訂各項次必須抽查的實體文件（槽檢合格證、出車前每日自主檢點表、SDS領用簽收簿、洗槽合格證明單與廢液聯單、原廠每年校正酒測日誌、車隊卡購油單等）。
    2. 防呆與扣分陷阱：明訂【一票否決項】（槽檢過期、出車酒測未落實/非0.00、危運證過期、防護裝備缺漏）以及廠商最常造假之漏洞（出車檢點表同一筆跡連打30天勾、車上SDS超期未更新）。
  - **產出實體工具**:
    - 生成 A4 橫向最佳化、可直接列印帶至現場打分之 Excel 表單：`C:\GOOGLE ANGET\槽車運輸外包商現場稽核評鑑表_資材實戰版.xlsx`。

* **Google Drive 專案備份「00_最近7天收工快照」滾動封存防爆機制健全化:**
  - **歷史快照自動封存歸檔**: 解決先前快照目錄超期堆積之問題，將超過 7 天（10/01 ~ 10/13 共 14 個資料夾）自動轉移至 `01_歷史按月封存\2026年10月\`，快照目錄僅保留 7 天內乾淨快照。
  - **專案備份外層雜項清理**: 將先前散落於專案備份根目錄之資料夾（`flowchart-web`、`AI影音自動剪輯工作站`、`IPA_2_PWA_App版_20261015` 等）歸位至 `02_歷史子專案備份\`。
  - **同步腳本升級**: 健全 `sync_drive.py` 與 `AutoSync_OffWork_Drive.ps1`，加入日期間隔推算與自動歸檔，確保往後每次收工備份均自動滾動維持 7 天快照窗口。

* **ACT 動態生產排程與進耗存整合系統 (`act-planner-pwa.pages.dev`):**
  - **槽車車號手動修正與接續排序功能 (100% 還原 GAS 圖二標準行為)**:
    1. **點擊即可手動修正**: 在「槽車出車動態排程表」的「指定槽車車號 / 標籤」欄位，未修正時保持預設輪替車號（如 E52, E53, E54）；點擊或聚焦即可直接輸入新車號（支援 Enter 快速儲存）。
    2. **黃色醒目覆寫外觀**: 手動修正後，該車次自動變換為溫暖黃底（`bg-amber-100 border-amber-400 font-black text-amber-950`），並於下方浮現兩枚操作按鈕：
       - `[接續排序]`: 以此手動車號為基準點，在出車順序清單中找到該車號後，將後續所有車次依循環順序順延推算（點擊後顯示高亮 `✓ 已接續`）。
    3. **雙向狀態持久化與雲端同步**:
       - `appState.manualCarOverrides` 與 `appState.sequenceShiftOverrides` 雙向納入 localStorage 快取與 Google 試算表 DataStore 資料庫。
       - 清空資料（`recalculateAll(true)`）或重設全表時一併乾淨清理。
    4. **排程開機時間與出料時間切換產品持久化修復**: 新增 `formatDateTimeLocal(val)` 自動標準化消除 ISO 時區 `Z`，切換產品參數雙向平滑繼承。
    5. **Excel 匯出自動淨化**: `exportToExcel()` 匯出前自動克隆 DOM 並純化車號欄位內容，排除按鈕文字，產出整潔乾淨的槽車排程 Excel。
  - **欄位輸入打字跳出修復與標題版本更新日期顯示**:
    1. **打字跳出 (Focus Loss) 根因與修復**: 原全表格欄位（進貨量、調撥、預估使用量、生產量、出料、槽桶存量、上限）綁定 `oninput` 事件，導致使用者輸入任一數字瞬間觸發 `recalculateAll` 並執行 `table.innerHTML = html` 全表重新渲染，將原本聚焦的 input 節點銷毀致使游標跳出中斷。現已全數改為 `onchange`，並配備 `onfocus="this.select()"`（點入即選取全文）與 `onkeydown="if(event.key==='Enter') this.blur();"`（Enter 鍵失焦確認），打字過程中保證游標穩定不跳出。
    2. **標題旁醒目標記版本更新日期**: 於頂部標題旁新增高辨識度黃金版本徽章 `v1.6 (2026/10/21 修訂)`，一目了然系統發布進度。
    3. **PWA 版本升級**: 快取版號升級為 `act-pwa-v1.6`，已部署至 Cloudflare Pages。

* **HTTPS 遠端網頁穿透中心動態發布與開機自動常駐升級:**
  - **遠端畫面黑框消除與雙軌文字注入修復 (main.py, static/index.html)**:
    1. **消除 Chrome/Edge/Terminal 畫面黑框**: 未鎖定狀態下全面使用原生 ImageGrab，徹底消除先前視窗被 PrintWindow 捕捉為黑方塊的問題，畫面清晰還原。
    2. **雙軌文字注入 (64-bit 原生剪貼簿 + SendInput UNICODE)**: 支援 Win32 64-bit 原生剪貼簿注入搭配 Ctrl+V，100% 支援任意中英文長字串、標點符號與多行文字；並以 SendInput UNICODE 作為第二道防護。
    3. **點擊強制奪取焦點 (Alt Key Trick)**: 點擊遠端視窗時自動透過 Win32 模擬 Alt 鍵繞過 Windows 前景鎖定限制，確保滑鼠點擊立即啟動該視窗並接受鍵盤文字輸入。
  - **穿透網址全域雙向發布機制 (`publish_tunnel_url`)**:
    1. 當 `cloudflared` 生成 Quick Tunnel 網址後，系統自動於本地根目錄與 Google 雲端硬碟 (`G:\我的雲端硬碟\`) 雙向同步生成現代化自動轉址頁面 `最新遠端穿透網址.html` 及純文字 `最新遠端穿透網址.txt`。
    2. 無論身在何處，只要開啟手機 Google Drive 點擊 `最新遠端穿透網址.html` 即可 2 秒自動跳轉至主機 Web 控制台。
  - **開機自動背景靜音常駐與守護工具**:
    1. 提供 `註冊開機自動啟動穿透.bat` 與 `取消開機自動啟動穿透.bat`，透過 `run_silent.vbs` 實現開機無黑框背景靜默守護。
    2. 提供 `kill_git.ps1` 與 `一鍵清除卡死git與釋放CPU.bat`，徹底解決 Windows NTFS 下 git 程序因背景鎖定佔用 CPU 之問題。

* **避坑指南 (Cross-Device Pitfalls):**
  - **Google Drive 雲端同步虛擬盤延遲**: G 槽為 Google Drive 串流虛擬磁碟，執行大規模檔案搬移時，避免多個 robocopy 或 PowerShell 同時存取同一路徑，改以循序判載移動最為穩健。
  - **二進位評鑑與分析表管理**: 新生成的 `.xlsx` 檔案必須以 `git add -f` 強制納管，避免受 `.gitignore` 阻擋而遺失於跨機環境。


## 前次進度與交接事項 (2026-10-20 Chrome遠端離線診斷與HTTPS純網頁穿透中心建立、教育訓練教材PWA化、中央大腦全域規範)
* **Chrome 遠端桌面 (Chrome Remote Desktop) 離線根因深度排查與診斷:**
  - **診斷結果與根因分析**:
    1. **UDP 19302 (STUN/ICE) 被公司防火牆封鎖**: Chrome Remote Desktop 依賴 WebRTC STUN 伺服器進行點對點穿透打洞。實際測試 `stun.l.google.com:19302` (UDP) 遭遇丟包超時。
    2. **Windows Schannel 憑證清單吊銷阻擋**: 內網 Schannel 出現 `0x80092012` 錯誤，公司防火牆阻擋了外網 CRL/OCSP 驗證，造成離線下線後 ICE Renegotiation 逾時中斷，Google Directory 狀態凍結在下線時間 (17:33)。
    3. **解決方針**: 在不需請假或申請變更網管防火牆政策的前提下，打造「純 TCP 443 (HTTPS) 單向出站網頁穿透中心」，確保任何家用瀏覽器皆可隨時直連公司主機。

* **全新子專案：HTTPS遠端網頁穿透中心 (`d:\GOOGLE ANGET\HTTPS遠端網頁穿透中心\`):**
  - **系統核心架構 (FastAPI + Cloudflare Quick Tunnel)**:
    1. **單向出站 TLS 穿透**: 自動下載並調用 `cloudflared.exe`，強制設定 `--protocol http2` 走純 TCP 443，完美突破公司防火牆阻擋 UDP/QUIC 的限制，秒級生成全球專用 HTTPS 網址。
    2. **動態 Port 搜尋綁定**: 預設 Port 8002，若被佔用自動切換至可用 Port（8003, 8004...），無崩潰中斷風險。
    3. **本機狀態即時儀表板**: 整合 `psutil` 提供 CPU 使用率、記憶體負載、磁碟剩餘空間與主機運行時間。
    4. **Web 互動式終端機 (Terminal)**: 支援即時執行 PowerShell 與 CMD 指令，遠端除錯與管理無延遲。
    5. **全機全磁碟穿透檔案總管**: 突破單一目錄限制，自動動態枚舉全機可用實體/網路磁碟槽（`C:`, `D:`, `E:`, `G:`, `I:`, `O:`, `Z:` 等），具備資料夾即時瀏覽、檔案線上預覽（程式碼/文字編輯器）以及單鍵下載功能。
    6. **緊急關機控制端點**: 實作 `/api/shutdown` API 與網頁紅燈關機鍵，可於需要時直接從遠端將本機安全關機或重開機。
  - **企業級雙重安全防護 (2FA & 防暴力破解)**:
    1. **TOTP 雙重驗證 (2FA)**: 整合 `pyotp`，使用者需輸入密碼與 Google Authenticator / 2FA App 的 6 位數一次性動態驗證碼才能登入。
    2. **敏感金鑰嚴格隔離防呆**: 修正初始設計隱患，登入介面完全剔除任何 QR Code 或 TOTP Secret 明文，金鑰獨立保存在本機 `security_config.json`，杜絕任何公開外洩可能。
    3. **防暴力破解保護 (Rate Limiter)**: 密碼或 TOTP 連續錯誤 5 次自動鎖定 IP 15 分鐘，日誌即時警報。
    4. **短期安全 Session**: 登入成功簽發高熵值 Token，提供有效期限與登出清除機制。
  - **標準三件套與一鍵啟動規範**:
    - 具備完整 `README.md`（含架構圖與目錄樹）、`SKILL.md`、`setup_env.ps1`，以及 `啟動HTTPS遠端穿透.bat`。

## 前次進度與交接事項 (2026-10-20 教育訓練教材全面升級 Cloudflare PWA 邊緣版、串接 R2 物件儲存與 D1 無伺服器資料庫)
* **教育訓練教材全面升級 PWA 雲端邊緣版 (education-training-pwa.pages.dev):**
  - **架構重大升級 (徹底脫離本機 Python 伺服器)**:
    1. **告別本機伺服器**: 徹底解決先前桌機 FastAPI (Port 8000) 未啟動導致前端畫面顯示「尚無教材」之痛點，亦解決了 Windows cmd.exe 讀取 UTF-8/LF 批次檔時發生字節錯位噴錯（如 'nd'、'ho' 不是內部或外部命令）的問題。
    2. **雲端邊緣架構**: 全面重構為 Cloudflare Pages + Functions (functions/api/)，搭配 **Cloudflare R2** 物件儲存（貯體：training-materials）存放 98 份教材 Markdown 與全解析操作步驟截圖，免主機費用且 0 流量費。
    3. **D1 資料庫初始化**: 自動在 Cloudflare 建立 training-db（ID: d9ec0f4f-464a-4889-8494-10b34790e1aa），執行 schema.sql 建立教材目錄與 AI 提問歷史紀錄表。
  - **進階功能與教材庫 100% 完整還原**:
    1. **圖片標註與修改畫布 (ImageAnnotatorModal)**: 支援自由圈選紅框、步驟圓圈序號 ①②③、⚠️ 注意、❗ 重要 等醒目標籤、文字與指引箭頭，修改後一鍵直存雲端 R2。
    2. **AI 智能助教串流問答 (/api/chat)**: 邊緣直連 Gemini 2.5/3.5/3.8 Flash，透過 SSE (Server-Sent Events) 提供毫秒級打字機串流回覆，並精準結合當前教材上下文 (RAG)。
    3. **AI 生成圖片 (/api/generate_image)**: 邊緣調用 Imagen 3 模型生圖，產出後直寫 R2 並自動插入教材。
    4. **Lightbox 燈箱放大**: 教材內任一圖片點擊即全螢幕清晰檢視。
    5. **98 份完整教材就位**: 涵蓋一階調撥、地磅單維護、出貨單維護、雜項庫存收料、雜發、庫存異常變更、請購單、採購收貨、工單結案、批號維護、客戶建立等。
  - **PWA 獨立 App 標準規範落地**:
    1. 實作 manifest.json 與雙尺寸圖示（192x192、512x512）。
    2. 整合 sw.js 離線快取服務，內建頂部智慧安裝橫幅，支援電腦與手機一鍵安裝為原生視窗 App。

* **中央大腦 (my-ai-brain) 規範升級:**
  - 於 INSTRUCTIONS.md 新增 **第 12 條：大型 Git 倉庫跨機防死結與效能最佳化規範**。
  - 明確規範桌機垃圾回收 (git prune + git gc --prune=now)、筆電端核心快取 (core.fscache) 與 IDE 背景盲目輪詢停用（解決多個 git.exe 堆疊卡死問題）。
  - 明確規範筆電全新 Clone 需使用 Blobless 瘦身拉取 (git clone --filter=blob:none)，以及嚴格禁止巨型影音檔進庫。
  - 已同步推送至遠端中央大腦庫：shihwei0809/my-ai-brain (Commit: 8878343)。

## 前次進度與交接事項 (2026-10-19 資材課移工派工適配系統上線、ACT 動態生產排程與進耗存整合系統全面升級 Cloudflare PWA 邊緣版與 Google 試算表雲端同步)
* **ACT 動態生產排程與進耗存整合系統全面升級 PWA 雲端邊緣版 (`act-planner-pwa.pages.dev`):**
  - **架構升級 (GAS 轉 Cloudflare Pages + Google 試算表雙向同步)**:
    1. 將原先受限於 Google Apps Script 執行效能與 iframe 限制的前端介面，全面遷移獨立至 **Cloudflare Pages** 邊緣網路 (`https://act-planner-pwa.pages.dev`)，後端資料庫繼續使用使用者 Google 試算表 (`AKfycbwTJm7TaEHqeEFrpVjUJpjDY3t60RXtpXsYRuFnflyKxtjqdGnFHhrFvjeYnu710aiRVQ/exec`)。
    2. 解決 CORS 跨域限制：前端以 `fetch(..., { mode: 'no-cors' })` 保持高可靠觸發，並透過 localStorage 與試算表雙重備份。
  - **PWA 漸進式網頁應用程式 (Progressive Web App)**:
    1. 配置標準 `manifest.json` 與雙尺寸圖標（192x192、512x512）。
    2. 建立 `sw.js` Service Worker，快取所有靜態核心資源與 CDN（Tailwind、SheetJS），支援斷線/弱網環境下離線推算。
    3. 實作 PWA 一鍵安裝機制（`beforeinstallprompt` 監聽與頂部「📲 安裝桌面 App」按鈕），電腦端與手機端皆可免安裝安裝為原生 App 視窗。
  - **排程推算核心優化**:
    1. **首日開機與次班出料自動計算**: 首日開機 08:00、製程出料 16:09 時，精確計算運轉時數與管線底料，首日算出 14.0T 耗用與 9.4T 生產。
    2. **小數點 0.1T 全流程精度**: 克服四捨五入整數日累積誤差（每日 30.3T 耗用、28.8T 生產）。
    3. **幽靈空值修復**: 手動清空格子刪除時即時釋放 `manualData[date]`，自動恢復系統動態推算。
    4. **目標產量動態展延與末日補尾數**: 支援 200T 等自訂目標，動態展延至 10/22 (30.3T) 與 10/23 補尾數 (14.7T)，完工後才顯示 `-`。
    5. **槽車排程連動**: 上方「槽車出車順序」清空時，下方槽車動態排程表自動同步清空，不再擅自生成殘留車次。
  - **標準三件套與一鍵發布**:
    - 本機路徑：`C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統\`
    - 具備 `README.md`（完整目錄樹與架構）、`SKILL.md`、`setup_env.ps1`，以及 `一鍵部署至Cloudflare.bat`（一鍵發布至 `act-planner-pwa`）。

* **資材課外籍移工派工與適配性管理體系:**
  - **核心場景適配性劃分 (槽車洩料 vs 包材出貨)**:
    1. **包材出貨作業 (高適配 70%~75%)**:
       - 搬運堆疊 (95%)、打包打帶纏膜 (90%)、外觀初步檢查 (75%) 可高度交由外勞執行。
       - **關鍵作業調整**: 資材**無需貼出貨標籤**（免除看中文字障礙），改為**貼繳庫單與條碼對刷**（適配度提升至 65%），依賴條碼槍「嗶一聲綠燈OK / 長鳴紅燈立即停機通報」落實物理防呆。
       - 系統帳務過帳 (ERP扣帳/單據簽收) 嚴禁外勞接觸 (0%)，100% 由本籍資材把關。
    2. **槽車洩料作業 (雙人協同制 35%~40%)**:
       - 車輛引導與前後輪擋 (90%)、靜電接地夾與集液盒鋪設 (85%)、管具 5S 清潔 (80%)、卸料重管抬搬 (60%) 由外勞操作。
       - 入料槽號確認 (如TK-624) 與親自開閥開泵、品檢取樣比重確認、緊急指揮等，嚴禁外勞獨立操作，落實本籍主管「上鎖掛牌 (LOTO)」與「雙人指差確認制」。
  - **交付成果與實體檔案**:
    1. **SOP 規範書**: `資材課_外籍移工作業劃分與SOP指差確認規範.md`。
    2. **工時統計 Excel 活頁簿**: `資材課_外籍移工工作適配性與工時統計表_v2.xlsx`（含作業權責矩陣表與每日 800 分鐘動態工時計算）。
    3. **現場中越雙語圖卡海報**: `資材課_中越雙語_條碼對刷與貼單SOP圖卡.png`（1920x1080 印刷級，含四大步驟與聲光紅綠燈警示）。
    4. **互動式 Web 派工系統**: `說明書/projects/material-labor-dispatch/index.html`（含三大功能分頁：適配矩陣、工時試算拉桿模擬器、圖卡預覽下載）。

## 前次進度與交接事項 (2026-10-18 新增 AI 影音自動剪輯工作站、語意多鏡頭實拍配圖引擎、整合 claude-motion-explainer)
* **AI 影音自動剪輯工作站 (`C:\GOOGLE ANGET\AI影音自動剪輯工作站`):**
  - **核心功能落地**:
    1. **素材與文字全自動剪輯**: 使用者上傳初始素材（圖片或短片）並輸入解說概念後，自動裁切構圖為 9:16 IG Reels / YouTube Shorts 規格。
    2. **Edge-TTS 語音與雙層字卡合成**: 整合微軟 Edge-TTS 雲哲男聲／曉臻女聲，免 GPU 零成本生成廣播級旁白，並動態繪製膠囊標題卡與半透明字幕條。
    3. **四幕連續分鏡智慧拆解 (Storyboard)**: 根據輸入主題（如化工廠、特斯拉超跑、通用主題）自動產生 4 幕連續分鏡劇本與對應視覺關鍵字。
    4. **精準語意照片檢索引擎 (Semantic Vision Matcher)**:
       - 解決隨機圖片與文字不符之問題。
       - 分鏡 2~4 自動依據每一幕台詞檢索高畫質真實攝影照片（如化工廠反應塔、防護衣工程師、風洞氣流、火箭噴嘴），自動縮放與裁切為 1080x1920 並施加電影級暗角與 Ken Burns 微推鏡。
       - 100% 免費無額外 API 費用。
    5. **FFmpeg 多分鏡無縫串接**: 獨立渲染各鏡頭片段後無縫 Concat 合併為 25~30 秒完整大片。
  - **遵循專案標準規範**:
    - 完整具備標準三件套：`README.md`（含目錄樹）、`SKILL.md`（AI 代理說明書）、`setup_env.ps1`。
    - 具備通用啟動檔 `啟動AI影音剪輯工作站.bat`（含 Python 偵測、套件修復、Port 自動切換、自動開瀏覽器）。
* **開源技能庫整合 (`claude-motion-explainer`):**
  - 成功 Clone `https://github.com/mathruffian-dot/claude-motion-explainer` 至本機，確認 Antigravity 與本地環境（Python 3.14 + Node v24 + FFmpeg 8.1.1）可完整相容該工作流。

## 前次進度與交接事項 (2026-10-17 專案大廳大改版、三大旗艦PWA系統納管上線、溫度通報轉移至 Cloudflare Pages)
* **專案大廳與說明書中心 (`agent-portal` & `說明書`):**
  - **三大旗艦 PWA 系統正式納管進大廳**:
    1. **IPA 專用動態生產排程與進耗存整合系統 (`ipa-pwa-app.pages.dev`)**: 採用 Advanced Mode (`_worker.js`) 直連 Cloudflare D1，支援多分頁 Excel 日報匯入、負庫存赤字遞延繼承與跨廠槽位分配。
    2. **倉庫常用包材管理與盤點系統 (`eshine-package.pages.dev`)**: PWA 離線快取 (`package-pwa-v2`)、行動走動盤點，並新增「📥 歷史帳卡一鍵匯出 Excel」對帳明細匯出功能。
    3. **回收液入料記錄系統 (`recycle-feed-records.pages.dev`)**: Cloudflare D1 毫秒級跨機秒同步、照片自動依 ISO 週分類歸檔至 Google Drive、Stale-While-Revalidate 秒開與密碼鎖防護。
  - **說明書資料庫擴充與重構 (`manuals_db.js`)**:
    - 新增上述三大系統之完整操作手冊，手冊總庫數量擴充至 40 份。
  - **溫度通報系統網址全面遷移至 Cloudflare Pages**:
    - 原 Firebase 網址 `https://hongsheng-temp-523.web.app` 全面遷移至最新雲端邊緣版：`https://weather-monitor-pwa.pages.dev/`。
    - 同步更新大廳卡片與溫度通報操作手冊對應架構說明。
  - **雙平台正式發布**:
    - ☁️ Cloudflare Pages 線上大廳：`https://google-agent.pages.dev`（已同步推送到獨立展示庫 `agent-portal`）。
    - 🟠 Netlify 正式線上大廳：`https://cerulean-praline-6b314d.netlify.app/`（已成功發布）。

## 前次進度與交接事項 (2026-10-16 流程圖系統 2.5D 立體混合調合充填流程圖上線、實體尺規表雙向換算與自訂 2.5D 元件)
* **儲槽製程流程圖系統 (`flowchart-web`):**
  - **現場實體儲槽尺規換算表 (Strapping Table) 深度整合**:
    - **問題根因**: 過去日報匯入時，針對大於 100 的實測數值一律寫死除以 6000mm 換算百分比，導致 500KL 級 (如 TK-624 實測 8447mm / 滿槽 9200mm) 被算成 140% 或溢出截斷，反推換算高度與重量 (KG) 出現偏差。
    - **解決方案**: 
      1. 建立 `TANK_STRAPPING_TABLE`，納入現場全系列儲槽的底面積比率 (`L/mm`)、桶底死容積 (`bottomVol`)、滿槽最高液位 (`maxLevel`)。
      2. 撰寫 `calculateFromTankHeight` 與 `calculateFromTankPercent` 雙向換算函式。
      3. 在「📊 液位記錄」彈窗中新增「實測高度 (mm)」輸入欄位，輸入 mm 即自動雙向同步計算 % 數、KL 與 KG (密度 0.785)；儲存時立即連動畫布水位。
      4. 點擊任何儲槽卡片時，視窗直接顯示「換算實體高度 (mm / maxLevel)」、「換算容積 (L / KL)」與「淨重 (KG)」。
      5. 改造 `importLiquidLevelExcel` 日報匯入函式：自動匹配槽體型號尺規，保存實測真實 mm 與公斤數至節點。
  - **第 10 分頁：混合調合與充填製程流程圖 (Mixing & Filling PFD) 上線**:
    - 完整復刻現場配方混合 PFD 流程：
      1. **RM-A**: 立體黃色原料箱體 (每月檢 Metal / 每批檢 水阻值)。
      2. **RM-B, C, D, E**: 藍色/白色立體圓柱桶群，頂部進料注口。
      3. **Mixing Tank**: 中央重型深灰圓柱反應攪拌槽，配備馬達傳動軸與即時液位動態波紋。
      4. **精密濾心組**: 3 聯式直立微孔濾心。
      5. **Drum 充填站**: 綠色木質棧板 + 4 桶 200L 鋼桶充填包裝 (前中後反壓監控)。
      6. **雙重循環迴路**: IPQC 小循環旁路回流 + 充填大循環防憋壓回流。
      7. **品質檢驗點 (Check Points)**: 紅色三角徽標 + 清晰規格條列，點擊任一元件或三角形即跳出檢驗規格彈窗。
      8. **管線動態流動修復**: 套用 `.pipeline.pipeline-active` 全域動態光束流動。
  - **全系統自訂 2.5D 立體元件擴充 (拖曳排版支援)**:
    - 在「➕ 新增儲槽 / 群組」面板新增 4 款 2.5D 實體模型選擇：
      - 🛢️ 2.5D 立體圓柱槽 (Cylinder Tank)
      - 📦 2.5D 立體原料箱 (Isometric Box)
      - 🪵 2.5D 棧板充填鋼桶 (Drum Pallet)
      - 🧪 2.5D 精密過濾心組 (Filters)
    - 支援自由拖曳排版、連線與大小縮放。
  - **發布驗證**:
    - 成功部署至 Firebase Hosting (`https://product-flowchart.web.app`)。
    - 獨立展示元件同步建立於 `mixing-filling-flow.html`。

## 前次進度與交接事項 (2026-10-15 專案維護、IPA 生產與採購跨電腦 D1 同步全面打通 & 鴻勝包材管理帳卡匯出 Excel)
* **Cloudflare Pages D1 跨電腦即時同步全面打通 (`ipa-pwa-app` - v3.11):**
  - **問題根因定位**:
    1. 使用者在不同電腦開啟 `https://ipa-pwa-app.pages.dev` 時，資料顯示為預設值或空白，且點擊儲存未寫入 D1 Studio。
    2. Cloudflare Pages 專案的 Root Directory 設為子目錄 `IPA 專用動態生產排程與進耗存整合系統/2_PWA_App版`，在包含中文、空格且無 Build Command 的 Monorepo 架構下，Pages 預設不會將 `functions/` 掛載為 API 路由。
    3. 發出 `/api/data` 請求時，伺服器退回到 SPA 前端靜態頁面 `index.html` (200 OK + `text/html`)，造成前端 `res.json()` 拋出語法解析例外，靜默退回空空的 `localStorage`。
  - **解決與架構改造步驟**:
    1. **引進 Advanced Mode (`public/_worker.js`)**:
       - 於 `public/` 建立 `_worker.js`，無條件優先攔截 `/api/data` (GET/POST) 與 `/api/archive` (GET/POST)。
       - 完美綁定 `env.DB` (`ipa-pwa-db` / ID: `4710dda9-0b73-46ca-a47c-ef55e19d7b6f`)，執行 SQL 讀寫；其餘靜態資源走 `env.ASSETS.fetch(request)`。
    2. **建立 `public/_routes.json`**:
       - 明確宣告 `{"version": 1, "include": ["/api/*"], "exclude": []}`，確保 `/api/*` 必定由 Worker 執行，絕不退回 SPA HTML。
    3. **修復 Babel 白屏問題**:
       - 修復在 git rebase 衝突解決時 `index.html` 內 `fetchAllData` 函式多出的一個閉合大括號 `}`，恢復畫面正常渲染。
    4. **推進 Service Worker 快取**:
       - 升級至 `ipa-pwa-v3.11`，確保所有電腦強制更新至最新前端與快取。
  - **實測驗證通過**:
    - 線上直接以 HTTP 探測 `https://ipa-pwa-app.pages.dev/api/data`，成功返回 `200 OK` 及完整排程槽位 JSON 資料（包含 `safetyStock`、`tanksList`、`lines`、`tankInits`、`tankLimits`、`manualGridData`、`salesPlanData`）。
    - 跨電腦同步功能 100% 正式就緒。
* **鴻勝包材管理系統 (eshine-package - v13.6):**
  - **歷史帳卡匯出 Excel 功能**:
    - 在「🔍 帳卡」對帳查詢結果中，為各品項卡片加入 **`📥 匯出帳卡 Excel`** 綠色快捷按鈕。
    - 引入 SheetJS (`xlsx.full.min.js`) 函式庫，自動產生包含品名、品號、規格、匯出時間及完整對帳明細（日期、摘要、收入量/批號、資材發、分一/分二/生產發、出庫批號、結存、備註）之 Excel 活頁簿，並自動美化欄寬。
    - 升級 Service Worker 快取版本為 `package-pwa-v2`，確保使用者端強制獲取最新功能。
    - 專案目錄確認位於 `C:\GOOGLE ANGET\倉庫常用包材管理\2_PWA_App版`，已設定 Cloudflare Pages 自動連動部署（`https://eshine-package.pages.dev`）。
* **IPA 生產排程與進耗存整合系統 (PWA v3.8 ~ v3.9):**
  - **歷史存檔區與頂部按鈕排版破圖修復**:
    - 解決點擊「備份存檔」或特定螢幕解析度下，按鈕換行破圖（如「重置預設 \n 定」）問題，全面加入 `whitespace-nowrap`、`shrink-0` 與彈性響應式排版。
    - 下拉選單寬度最佳化為 `w-[160px] truncate`，移除重複雜亂的時間戳記，改為精巧格式。
  - **台灣時區 (UTC+8) 校正**:
    - 將存檔紀錄的時間裁切改為以本地瀏覽器解析並轉換為台灣時間 `MM-DD HH:mm`，解決格林威治 UTC 0 導致少 8 小時之 Bug。
  - **ershine 品牌 Favicon 與 PWA App Icons 補回**:
    - 補齊 `public/favicon.png` 與 `public/icons/icon-192.png`、`icon-512.png`，並在 `index.html` 補上正式 `<link rel="icon">` 與 `<link rel="apple-touch-icon">`。
  - **一廠共用原料池槽位排除/納入之動態重量增減防呆修復**:
    - 排查當取消勾選 TK693 時原料起算未扣減之問題，重寫 `toggleTankSharedPool` 加入雙重回退計算保護（若無日報快照時直接由當前該槽期初動態增減，有日報時自動重算現存勾選集合），點選即時扣減/加回。
  - **Cloudflare Pages 自動連動建置設定**:
    - 完成 Cloudflare Pages 與 GitHub 倉庫（`shihwei0809/google-agent`）之連動：根目錄指定為 `IPA 專用動態生產排程與進耗存整合系統/2_PWA_App版`，輸出目錄為 `public`，分支為 `main`。

## 前次進度與交接事項 (2026-10-14 歷史照片連結修復與雙雲端回寫強化 - v14-D1)
* **照片連結問題排查與徹底修復 (回收液入料記錄系統 - v14-D1):**
  - **原因定位**:
    1. 早上切換至 Cloudflare D1 後，`loadQueryRecords` 優先向 D1 抓取資料。
    2. 新提交的紀錄照片先非同步傳往 GAS (Google Drive)，但 GAS 原本未回傳 Drive 網址給前端，導致 D1 的 `t_before_url`、`v_photo_url`、`t_after_url` 為空值。
    3. 因 D1 回傳 200 OK，前端從未觸發 `catch` 區塊，因此覆蓋了 Google Drive 照片連結。
    4. **照片資料 100% 安全**：所有今日拍攝之照片皆完整存放於 Google Drive「回收液照片歸檔」資料夾與 Google Sheets 中，毫無遺失。
  - **修復步驟與架構強化**:
    1. **歷史資料即時補全**: 撰寫背景同步腳本，將 Google Sheets / GAS 中的所有 17 筆照片網址（含 10/14 今日 `HAB-6108/CO9`、`HAC-0156/645` 等）完整回補至 Cloudflare D1 資料庫。
    2. **GAS 回傳照片網址**: 修改 `Code.gs` 之 `handleBeforeFeed`、`handleCompleteFeed`、`handleAfterFeed`，在存檔至 Drive 後將網址包入 JSON 回傳。
    3. **自動回寫 D1**: 修改 `public/index.html` 之 `autoSync`，當照片上傳 GAS 成功後，自動呼叫 D1 API 之 `action: "update_photos"`，即時補填相片網址至 D1。
    4. **查詢歷史兜底防呆**: 改寫 `loadQueryRecords`，若 D1 回傳之完成紀錄中仍有缺少照片連結者，自動無縫向 GAS 權威資料庫回補。
    5. **版本升級**: 前端升級至 `v14-D1 (相片修復 2026/10/14)`，Service Worker 快取版本推進至 `recycle-d1-v14-photo-fix`。
* **Google Drive 照片自動依週分類歸檔功能 (回收液入料記錄系統):**
  - **需求背景**: 原本所有車輛/液位照片皆直接散放在 `回收液照片歸檔` 根目錄，檔案數量暴增後難以依週期檢視。
  - **自動依週歸檔機制**:
    1. 於 `Code.gs` 新增 `getWeeklyFolder(parentFolder, dateInput)` 與 `saveBase64ToDrive` 週分類邏輯，依上傳日期或拍照日期自動計算所屬 ISO 週數（如 `2026年第42週 (10.12~10.18)`），若該週資料夾不存在則自動建立，新進照片自動存放至所屬週資料夾。
    2. 新增 `organizeExistingPhotosToWeeklyFolders` 函式與 `organize_photos.js`、`一鍵將雲端硬碟照片依週分類.bat` 腳本。
    3. **實體驗收完成**：已將本機 `G:\我的雲端硬碟\回收液照片歸檔` 內現存的 59 個舊照片全數依日期安全移入 `2026年第42週 (10.12~10.18)`，所有 Google Drive 圖片分享連結與 ID 維持不變，各表單超連結 100% 正常。

## 前次進度與交接事項 (2026-10-14 晨間更新)
* **功能重大升級與架構轉換 (回收液入料記錄系統 - v13-D1 旗艦版):**
  - **資料庫全面轉移至 Cloudflare D1 (共用 `egups-db`)**:
    1. 解決免費資料庫配額問題，直接共用 `egups-db` (Database ID: `b87a145c-937d-430b-94f0-1962255abd04`)，並已在遠端完成 `recycle_records` 資料表結構初始化與雙向索引。
    2. 開闢 Cloudflare Pages Functions REST API (`/api/records`)，提供毫秒級原子事務操作（`before_feed`、`after_feed`、`complete_feed`、`query`、`delete_record`）。
  - **徹底修復按鈕「處理與壓縮中...」卡死 Bug**:
    1. 在 `beforeForm` 與 `afterForm` 提交流程加入 `try...finally` 保證結構。
    2. 無論 Canvas 壓縮照片或網路拋出何種例外，`finally` 區塊強制執行 `submitBtn.disabled = false` 並將文字恢復為「儲存」或「完成入料記錄」，絕不再卡死停滯。
  - **徹底消除後台刪除後的「孤兒幽靈筆」殘留**:
    1. 改寫 `loadPendingRecords`：當手機連線向雲端 D1 拉取真實 `pending` 清單時，主動以雲端現有單據為準。若後台已經刪除或已由其他同仁完成入料，手機端 IndexedDB 自動清除該筆孤兒資料，切換分頁立即清空消失。
    2. 在 `autoSync` 中加入 404 / `isDeleted` 自動清理機制：當上傳 `after_feed` 遇後台回傳 404（後台已被刪除），直接自主機端 IndexedDB 移除暫存，不再無窮重試。
  - **照片保留於 Google Drive**:
    - 照片 Base64 依然無縫非同步送往 Google Apps Script 歸檔於 Google Drive「回收液照片歸檔」資料夾，維持原有照片儲存方式，完全不需 R2。
  - **線上正式版發布**:
    - Cloudflare Pages 正式網址：`https://recycle-feed-records.pages.dev` (Service Worker 快取版本：`recycle-d1-v13`)。
    - 經本機 Node.js 與遠端 REST API 實測：`before_feed` 寫入、`after_feed` 更新、歷時計算（22 分鐘）與清單同頻 100% 驗證通過。

## 前次進度與交接事項 (2026-10-13 晚間收工更新)
* **功能重大升級與修復 (IPA 生產排程與進耗存整合系統 - v3.3 ~ v3.6):**
  - **日報 08:00 重量一鍵帶入 & 多分頁 Excel 直接匯入 (v3.5)**:
    1. 實作離線 SheetJS (`xlsx.full.min.js`) 整合，使用者可直接點擊「📂 匯入日報 Excel」上傳 `儲槽作業日報表2026.10月.xlsm`。
    2. 瀏覽器端秒讀解析所有分頁（如 `10.1`、`10.2`、`10.8`、`10.12`...），自動定位各槽 08:00 重量。
    3. 彈窗列出分頁清單，人員可點擊「⚡ 自動填入產銷 12 日起算」，系統自動填入當日槽重並切換至產銷排產模式。
    4. 同步快取至本機 `localStorage`，下拉選單持久保存。
  - **共用原料池負庫存赤字精確遞延累積修復 (v3.4)**:
    1. 排查發現共用池分槽扣減時採用 `Math.max(0, tempVal)`，庫存耗盡後未滿足之耗用（缺料赤字）被丟棄，導致次日各槽結存維持為 0，每天期初歸零無法累加。
    2. 新增未滿足耗用量遞延分配機制，將赤字按槽位均分記錄於各槽結存，次日期初精確繼承負數（如 10/24: 1 -> 10/25: -32 -> 10/26: -65 -> 10/27: -98 -> 10/28: -131）。
    3. 期初負值與結存赤字自動以紅字與紅底高亮警示。
  - **原採進貨文字解析修復與跨廠儲槽分配 (v3.6)**:
    1. 修正重量解析異常：原正則 `(?:MT|噸|T)?` 單位為選填，導致誤將 `CIF-5` 或 `FOB-6` 中的「5」或「6」誤判為重量；已改為強制匹配 `MT / 噸 / T`，精確解析 `175MT` 為 `175`。
    2. 修正單號批號貪婪吞入後方字元的問題，乾淨分離單號（如 `CIF-5 2609-I05`）。
    3. 支援「跨廠選擇儲槽」：上方預設儲槽與每列分配儲槽改為 `<optgroup>` 跨廠選單，無論當前在彰濱一廠或崙尾二廠，皆可自由分配至一廠 5 槽共用池、一廠獨立槽或二廠 `TK617` / `TK618`。
  - **正式發布與部署**:
    - 線上正式版 Cloudflare Pages: `https://ipa-pwa-app.pages.dev` (Service Worker: `ipa-pwa-v3.6`)。

## 前次進度與交接事項 (2026-10-13 更新)
* **功能升級與架構修復 (N系統報表產生 - v1.0.21):**
  - **地點智慧正規化**：支援人員輸入或排程含有「18廠p2」、「18p2」、「15廠p5」、「15p5」等各式寫法（包含含「廠」字、小寫 p、前後多餘空格/字詞），系統會自動正規化為標準代碼（如 18P2、15P5）並即時連動長代號與料號。
  - **Excel/CSV 匯入防呆強化**：標題欄位新增支援「到貨廠、到廠、廠別、卸料」等關鍵字與含換行/空格標題；並新增「全列智慧掃描地點」兜底機制，即使標題行錯位或無標題，也能精準從該列抓到對應地點，徹底解決匯入後地點空白的問題。
  - **UI 介面精簡**：取消「長代號」下拉選單改為純文字輸入框（移除下拉箭頭，地點輸入時仍自動帶出，亦可手動調整）；隱藏「料號 (自動)」顯示欄位（後台仍保留變數與對照邏輯，產出報表資料不受影響）。
  - **版本更新**：版本號升級至 `v1.0.21 (2026/10/13 更新)`。

* **功能升級與架構修復 (回收液入料記錄系統 - PWA v12 發布與全面穩定化):**
  - **解決安卓與 iPhone 同步狀態不一致**：排查後台刪除後安卓仍顯示未同步之原因（本機 IndexedDB 快取孤兒資料），新增頂部未同步管理彈窗，支援「立即手動重試」與「一鍵放棄並清除本機暫存」，並於 `finally` 保證清除傳輸鎖防卡死。
  - **解決「入料完成」卡頓問題**：全面採用 Stale-While-Revalidate（本地優先秒顯）架構，切換至「入料完成！」分頁瞬間 0 秒渲染本地暫存卡片，背景非同步平滑對齊雲端 GAS，操作員徹底擺脫 3~6 秒冷啟動轉圈等待。
  - **分頁名稱更名**：原「入料後記錄」更名為「入料完成！」。
  - **查詢歷史密碼鎖定保護**：切換至「查詢歷史」預設需輸入授權密碼（預設：`7588555`，支援 Enter 鍵快速解鎖），解鎖狀態保存在 `sessionStorage`，支援手動「重新上鎖」。
  - **PWA Service Worker 更新機制重大架構升級 (Network-First)**：
    1. 將原本的 Cache-First 改為 Network-First（網路優先策略），連網時優先抓取雲端最新資源並背景刷新快取，斷網時無縫退回本地快取，徹底杜絕舊版網頁死咬快取不更新、需手動清除後台快取的痛點。
    2. 新增 `controllerchange` 監聽，新版 SW 接管時 100% 必中彈出綠色更新橫幅。
    3. 標題列新增 `v12 (點我手動檢查)` 視覺徽章，點擊可主動呼叫 `reg.update()` 檢查更新。
  - **已推送到 GitHub 主支**：Commit [`4ce2a3b`](https://github.com/shihwei0809/google-agent/commit/4ce2a3b)。

* **功能升級與架構修復 (三合一單自動產生器):**
  - **地點代號對照表動態搜尋 (優先日期版)**：新增 `find_mapping_file`，優先辨識 `地點代號對照表-YYYYMMDD.xlsx`（帶日期且取最新修改者），次要比對 `地點代號對照表.xlsx`，並於狀態列即時顯示所讀取的實際檔名。
  - **出貨區動態廠區下拉選單**：對齊最新對照表結構，移除固定預設料號欄位，改為動態讀取 C 欄之後的所有欄位（彰濱一廠、彰濱二廠...），介面「出貨區 (選/貼)」改為 `ttk.Combobox` 下拉選單，並連動自動填入對應廠區料號。
  - **採購單號空白防呆修復**：修正 COA 產生邏輯（Excel B12 與 CSV 第 12 列），當介面採購單號留空時強制寫入空白 `""`，徹底清除範本預設單號。
  - **長代號回歸一對一純字串 Entry**：嚴格落實專案隔離，移除三合一單不適用的多代號 Combobox 下拉邏輯，長代號恢復為唯讀純文字框，輸入短代號立即一對一自動帶出。
  - **記憶上次開檔路徑機制 (`last_dirs.json`)**：整合開檔記憶，獨立記錄 Excel 排程、生產履歷 Chemical_Lorry 與 COA 表單/截圖的選取資料夾。
  - **一鍵更新批次檔防呆升級**：修復 Windows CMD 括號解析語法陷阱（`(MERGE_HEAD)` 導致的「這個時候不應有」錯誤），加入自動重設卡死機制，確保 pull 順暢不報錯。

## 前次進度與交接事項 (2026-10-12 傍晚收工更新)
* **功能修復與架構升級 (IPA 生產排程與進耗存整合系統 / 產銷排產模式 & Cloudflare PWA 雙軌):**
  - **產銷排產首日卡死問題徹底修復**：原邏輯以 `firstSalesDayIndex` 正向搜尋，導致填寫 10/12 時因 10/5 仍有值而始終卡在 10/5；現已改為 `latestSalesDayIndex` 倒序搜尋，自動以最新輸入之日期起算，使用者無需清空 10/5 即可由 10/12 起算。
  - **月曆輸入格視覺防呆強化**：當前起算日自動掛上 `[起算]` 紫色徽章並亮框，歷史舊日期淡化標記為 `(舊)`。
  - **排產雙核心引擎精準度純淨化**：起算日之前機台不扣料、不累加多餘下腳料，確保起算日庫存 100% 精確。
  - **雙系統分離與 PWA 雙軌落地**：產銷排產系統 (`IPA生產與採購`) 與獨立生產排程系統維持各自獨立；並為 PWA App 版補齊 `manifest.json`、`sw.js`、離線安裝橫幅、本機測試伺服器與 Word 操作手冊 (`build_manual_doc.py` 產出 `.docx`)。
  - **Cloudflare D1 與 GAS 雙雲端定位釐清**：Cloudflare Pages (`ipa-pwa-app.pages.dev`) 後端透過 Functions 連接 Cloudflare D1 資料庫，與 GAS 試算表各自獨立運作，雙軌並行無衝突。

## 前次進度與交接事項 (2026-10-12 下午更新)
* **功能升級 (三合一單自動產生器 & N系列報表輸出系統 - 一鍵更新批次檔革命性升級):**
  - **排查人員電腦 not a git repository 錯誤**：同仁電腦的資料夾為一般複製或由 NAS 拷貝（無 .git 庫），且主庫近 2GB，同仁不適用手動 git clone。
  - **雙模式智慧判斷一鍵更新**：改寫兩大專案的 一鍵更新系統程式.bat。
    1. Git 開發庫 (D 槽)：執行正規 git pull，更新成功後偵測 NAS (O 槽) 連線並提示一鍵發布至 NAS。
    2. 無 Git 一般環境 (同仁電腦 / NAS / 隨身碟)：使用 Windows 內建 PowerShell WebClient 直連 GitHub 下載最新 main.py，免裝 Git、免打指令，1 秒完成更新並開啟主程式。

## 前次進度與交接事項 (2026-10-12 下午追加)
* **儲槽作業日報 (原料槽液位疊圖比對與黃底標記):**
  - **精確比對標黃**：比對 `6. 製程參數_V13_原料槽液位疊圖_for 世偉.xlsx`（工作表：`液位疊圖_2`）與 `TK604_Report_v8.xlsx`（2026年 08:00 液位數值）。
  - **自動高亮差異**：當日數值差值絕對值 $\ge 50\text{ mm}$ 時，自動將原料槽 A/B 之百分比與換算高度欄位標記亮黃色底色（`#FFFF00`）。
  - **完整保留公式與圖表**：總計標記 596 個儲存格（A槽 138 筆、B槽 160 筆），並完整保留工作表原有的 4 張折線圖表與公式運算。
* **功能升級 (回收液入料記錄系統):**
  - **雙時間戳記與入料歷時統計**：後端 Google Sheets 新增 `入料前時間`、`入料後時間` 與 `歷時(分)`。
  - **離線真實時間精準記錄**：手機離線拍照時即時擷取客戶端精確時間戳記，連線同步時優先使用離線拍攝時間，杜絕時差。
  - **修復 UTC 跨時區與英文日期顯示**：徹底修復前端顯示 `Mon Oct 12 2026 00:00:00 GMT` 的問題，卡片優先顯示格式化之建立時間與入料時間。
  - **歷時視覺化徽章**：查詢卡片標題加入藍色 `⏱ 歷時 X 分鐘` 徽章。
  - **PWA Service Worker 快取版號**：升級至 `v11`。

## 前次進度與交接事項 (2026-10-12 上午)
* **功能升級 (QC-系統客製化電子化工廠 / Cloudflare D1 版):**
  - **T100 排程智慧增量去重防呆**：為解決生管分批或陸續補進貨 Excel 導致重複匯入的問題，前端與 Cloudflare D1 後端實作增量合併 (Upsert)。依「單號 doc_no + 品名 + 槽號」自動去重，已存在單據自動略過、新進貨單據自動補入。
  - **後端安全防護**：移除了原本粗暴的 `DELETE FROM T100_Orders`，改為安全增量合併，並為 D1 建立 `idx_t100_doc` 與 `idx_t100_date` 索引加速比對。
  - **版本可視化與一鍵檢查更新**：於首頁卡片標題及頁尾新增亮藍色版本號標籤 `🚀 v3.0.4 (2ed39b2)`，點擊即可主動向 Service Worker 檢查雲端更新並強制重新整理，方便人員隨時確認版本是否成功部署。
  - **PWA 快取版本**：推進至 `qc-kanban-v3.0.4`。

## 前次進度與交接事項 (2026-10-11)
* **功能修復 (QC-系統客製化電子化工廠 / 本地三合一單核對系統):**
  - **Error_Log 與 Teams 通知遺失修復**：排查人員核對失敗時未寫入試算表的問題，發現為 `processFormAndVerify_V10` 中核對失敗未呼叫日誌寫入所致。
  - **加入 Power Automate Teams 通知模組**：整合 `sendTeamsNotification`，當現場作業員核對失敗時，同步寫入試算表 `Error_Log` 分頁，並透過 Power Automate Webhook 推播警報至 Teams 頻道（包含人員、位置、槽號、時間、失敗詳細原因）。
  - **完整備份建立**：將原始版本與整合後版本分別備份至 `C:\GOOGLE ANGET\本地三合一\` (`code_original_backup.js` 及 `code_with_teams_errorlog.js`)。

## 前次進度與交接事項 (2026-10-10 追加更新)
* **功能新增 (鴻勝 三合一單自動產生器):** 
  - 於視窗標題列加入版本號與更新日期 (v2.2.1 - 2026/10/10更新)。
  - 新增 一鍵更新系統程式.bat，完整複製 n 系列的 Big5 編碼與指令邏輯，供人員免登入 GitHub 執行自動差分更新 (git pull) 並接續啟動主程式。

## 前次進度與交接事項 (2026-10-10 補充)
* **功能修改 (鴻勝 三合一單自動產生器):** 將本機版 GUI 視窗改為自適應寬度 (Auto-resize)，讓文字輸入欄位可隨視窗拉伸自動展開 (weight=1)，並排除「項次」、「產生」、「清空單列」等小欄位避免變形過大。

## 前次進度與交接事項 (2026-10-09)
* **功能新增 (Cloudflare D1 版):** 實作 30 秒自動背景更新機制。移除了 index.html 中僅限 GAS 環境 (IS_GAS) 才能定期抓取資料的限制，讓 Cloudflare D1 版也能背景定時 load() 刷新前端資料，避免使用者需要手動 F5 重新整理。
* **PWA 更新:** 將 Service Worker 快取版本號推進至 3.0.3。
* **部署與備份:** 已透過 Wrangler 強制部署至 Cloudflare Pages 正式環境，並完成本日收工 Git 推送與雲端硬碟備份。


