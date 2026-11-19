# 跨電腦交接日誌 (HANDOVER)

## 今日進度與交接事項 (2026-11-19 勝一/鴻勝四大報表系統全面升級：勝一小包三重核對與F5標準化、COA回推1天、自訂預設輸出位置、一鍵更新雙重備份與一鍵秒還原保護)
* **勝一專用版 - 小包系統報表產生 (`小包系統報表產生_勝一\main.py`):**
  - **COA `ShipQty` 與 `CoACompletionDate` 規則更新**:
    1. `ShipQty` 一律採用 **`桶數 * 200`** 計算寫入。
    2. `CoACompletionDate` 一律採用 **`DeliverDate - 1 天`** 自動回推寫入（支援跨月、跨年日曆換算）。
  - **生產履歷 (PR) 匯入與產出「批號 + 出貨日 (DeliveryDate) + FabPhase」三重核對 & 禁止覆寫**:
    1. 載入與產出時均對齊「批號 + 出貨日 + FabPhase」三重核對，支援雙條件 `(地點, 品名)` 查表。
    2. **PR 保留原值不覆寫**：生產履歷既已通過核對，保留母表人員手打之原值，**不引用對照表覆寫**；**僅 COA 之 `FabPhase` 由對照表寫入**。
  - **徹底移除舊版硬編碼 `125A` / `1200` 猜測邏輯**:
    1. 移除 `deduce_fab_phase` 查表落空後寫死 `if s == "5廠": return "125A"` 等硬猜代碼，嚴格以《台積小包材地點代號對照表.xlsx》為唯一準則。
    2. 若代號表查無對應 `FabPhase`，回傳空字串並彈出警告提醒人員至代號表新增或修改，絕不硬寫入錯誤代號。
  - **檔名、中間層廠區資料夾與最裡層資料夾全面標準化為 `F5` 及帶入品名**:
    1. 針對台積 5 廠（簡稱 `5` / `5廠` 或代號表 Phase 為 `F5`），中間層資料夾由 `5` 統一標準化為 **`F5`**。
    2. 最裡層資料夾加上品名，格式為 **`{月日} {廠區代號} {品名} {批號}`**（例如：`...\F5\1119 F5 SEP73E4 26B12PE4D1\`）。
    3. PR 與 COA 產出檔名中之廠區代號亦統一為 **`F5`**（如 `PR_L269000_75970680_F5_Shiny20261119.xlsx`、`COA_L269000_SEP73E4_F5_20261120.csv`）。
* **勝一小包、鴻勝三合一、鴻勝 N系列小包 — 新增「⚙️ 預設輸出放置位置」自訂選擇器 (100% 獨立隔離)**:
  - 於 `小包系統報表產生_勝一\main.py`、`三合一單自動產生器\main.py`、`n系統報表產生\main.py` 介面新增：
    - `📁 預設輸出放置位置` 輸入框、`📂 選擇位置...` 按鈕與 `↺ 還原程式目錄` 按鈕。
    - 每套系統各自獨立儲存於該資料夾下的 `last_dirs.json` (`output_dir` 鍵值)，鴻勝與勝一資料 100% 實體隔離絕不混用。
  - 修復 `三合一單自動產生器\一鍵更新系統程式.bat` 歷史下載網址誤指到 `n系統報表產生` 之問題。
* **四大系統 (`小包系統報表產生_勝一`、`勝一三合一單產生系統`、`三合一單自動產生器`、`n系統報表產生`) 實裝「更新前雙重備份 + 語法自我檢測 + 一鍵秒還原」機制與 `.bat` 閃退根治**:
  - **排查修復 `.bat` 雙擊沒反應/閃退根因**：
    1. **根因 1 (`chcp 65001` 置於 `cd /d "%~dp0"` 之前)**：Windows `cmd.exe` 啟動時以預設 CP950 展開 `%~dp0` 中文資料夾路徑（如 `小包系統報表產生_勝一`），若先執行 `chcp 65001`，`cd /d "%~dp0"` 會將 CP950 位元組誤當 UTF-8 解析導致 `The system cannot find the path specified.`。
    2. **根因 2 (`.bat` 內含 UTF-8 多字節中文與 LF 換行)**：導致 `cmd.exe` 在 `if (...)` 區塊內發生 byte-offset 偏移，截斷指令（`.DownloadFile(' was unexpected`）並瞬間關閉視窗。
    3. **終極解決方案**：將四大系統的 `一鍵更新系統程式.bat` 與 `一鍵還原上一版程式.bat` 全面改為 **100% 純 ASCII (`0x00-0x7F`) + 嚴格 CRLF (`\r\n`)**（並新增 `.gitattributes` 鎖定 `*.bat text eol=crlf`），第一行直接執行 `cd /d "%~dp0"`，再由 Python Base64 內嵌引擎執行備份、雲端下載、語法檢查與繁體中文主控台輸出，徹底杜絕任何 Windows 語系或換行閃退問題！
  - **升級各系統之 `一鍵更新系統程式.bat`**：
    1. 更新前強制將現有正常 `main.py` 雙重備份至 `main_backup_last.py` 與 `backups\main_backup_YYYYMMDD_HHMMSS.py`。
    2. 下載或同步後自動執行 `py_compile` 語法檢測與檔案大小驗證，異常時自動攔截並退回原版，完成後自動啟動 `main.py` 視窗。
  - **新增各系統之 `一鍵還原上一版程式.bat`**：
    - 若線上更新版本有任何問題，人員雙擊即可在 1 秒內將 `main_backup_last.py` 還原回 `main.py` 並自動重啟系統。

---

## 今日進度與交接事項 (2026-11-18 台積三合一單與 COA 雙重核對系統 V50：實裝 5 重防呆攔截誤拍三合一單、強制卡控磅單ESXM特徵、PWA Service Worker快取升級與D1測試資料修正)
* **台積三合一單與 COA 雙重核對系統升級至 V50 (`第二類_生產管理與API串接\三合一單-to-PHP-Migration` | 線上網址: `https://coa-check-pwa.pages.dev`):**
  - **問題根因分析與防呆漏洞修補**:
    1. **三合一單文字重疊漏洞**：先前系統在關卡 2 (地點)、關卡 3 (槽號)、關卡 4 (系統批號) 僅單純檢測字串是否存在。由於勝一三合一單條碼紙上本來就同時印有地點 (`EF150L154`)、槽號 (`5E308`)、批號 (`626B17E3081`)、料號 (`4L12C53161`)，若現場作業員偷懶或故意拿三合一單當作地磅照片拍攝，先前系統會誤判為全數相符而顯示「核對成功」（即歷史紀錄中單號資訊為空白 `-` 的假成功紀錄）。
    2. **實裝 5 重嚴格防呆卡控機制**：
       - **防呆 1 (地磅誤拍三合一單)**：檢測照片 OCR 是否包含 `TSMC LORRY MATERIAL BARCODE`、`勝一化工條碼`、`符合出貨規格(SPEC)`、`CHEMICAL LORRY`、`GAS TRAILER`、`填表人 (supplier)` 等三合一單專屬關鍵字，命中直接 100% 阻斷判定失敗！
       - **防呆 2 (地磅單真實特徵卡控)**：地磅照片必須含有台積電出貨過磅單編號（`ESXM201-...`）或地磅/過磅單特徵（`ESXM`、`過磅`、`地磅`、`磅單`、`毛重`、`淨重`、`皮重`、`TRUCK SCALE`）。未具備者直接阻絕。
       - **防呆 3 (地磅誤拍 COA 報告)**：檢測是否誤將 COA 報告書（`SCHEMANAME`、`SHELFLIFETIME`、`COACOMPLETIONDATE`）拿去當地磅拍。
       - **防呆 4 (COA 誤拍三合一單)**：檢測 COA 照片是否誤拍成三合一單。
       - **防呆 5 (照片重複偵測)**：COA 照片與地磅照片若為同一張照片（OCR 文字重疊率過高），直接攔截。
  - **PWA Service Worker 快取問題根治 (升級 V50)**：
    1. **快取名稱升級為 `coa-check-pwa-v50`**：解決手機離線 PWA 預設固化快取導致執行舊版程式之問題，新版啟動自動抹除舊快取。
    2. **前端自動更新與手動刷新**：`index.html` 頂部標題明確標註「核對系統 V50 防呆升級版」，新增「🔄 檢查更新」按鈕，並整合 `reg.update()` 於背景自動偵測最新版並無感重整。
    3. **歷史看板資料庫校正**：自動將測試誤判之 ID 266 與 ID 268 更新為 `防呆攔截-測試作廢 (誤拍三合一單)`，看板不再顯示假成功。
  - **全端同步**：已同步更新 Cloudflare Pages Functions (`verify.js`, `query.js`)、PWA 前端 (`index.html`, `sw.js`)、PHP 後端 (`process.php` & `1_Web_網頁版`) 及 Google Apps Script (`Code.gs` & `本地三合一`)。Cloudflare Pages 已成功部署上線。

---

## 今日進度與交接事項 (2026-11-18 鴻勝化學 QC 看板升級 v3.3.7：TSC LAN 192.168.3.128 雙軌直印、免裝Python零依賴電腦代理與手機秒出紙)

---

## 今日進度與交接事項 (2026-11-18 鴻勝化學 QC 看板升級 v3.3.7：TSC LAN 192.168.3.128 雙軌直印、免管理員權限純TcpListener零依賴代理與手機秒出紙) (feat(三合一單): 實裝5重防呆攔截誤拍三合一單、強制卡控磅單ESXM特徵、PWA升級V50與D1測試資料修正)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.7 (`第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **手機跨網段 (192.168.38.X -> 192.168.3.128) 終極解決方案**:
    1. **免管理員權限、零依賴 Windows 代理 (`一鍵啟動TSC標籤列印服務.bat` + `tsc_print_proxy.ps1`)**：
       - 克服原 `System.Net.HttpListener` 在非管理員環境會被 Windows 權限封鎖（Access Denied）的問題，改採 .NET 原生 `System.Net.Sockets.TcpListener` 監聽 Port `8099`。
       - 任何一般使用者帳號雙擊 BAT 即可秒啟動，自動偵測並印出電腦本機 IP（如 `192.168.11.199`）。
       - 完美處理 HTTP POST `/print` 與 CORS 預檢請求（OPTIONS），接收 TSPL 字串後以 Big5 編碼直通印表機 `192.168.3.128:9100`。
    2. **看板新增綠色「🚀 TSC 90x60 一鍵直印」按鈕**：
       - 手機在列印視窗點擊綠色直印按鈕，直接將標準 TSPL 丟給電腦代理出紙。
       - 徹底避開手機瀏覽器邊距、等比縮放、紙張選項鎖死與跨網段連不到印表機的所有問題！
    3. **雙軌相容**：保留「🖨️ 瀏覽器列印」，一般電腦或已開通網段之裝置依然可正常彈窗列印。
  - **發布與推送**：升級至 `v3.3.7`，更新 Service Worker 快取名稱為 `qc-kanban-v3.3.7-offline`，重新產出 Word 操作手冊，已順利部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 今日進度與交接事項 (2026-11-18 鴻勝化學 QC 看板升級 v3.3.6：採納方案 A 採用 TSC 原廠 100% 免費無廣告 Print Utility 行動列印 90×60mm)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.6 (`第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **採納方案 A（100% 免費無浮水印、原廠官方直通）**:
    1. **全面採用原廠官方 App `TSC Print Utility`**：徹底移除第三方付費/浮水印疑慮的 RawBT 方案，Android 與 iPad 一律對齊原廠官方 App。
    2. **規格鎖定 90mm × 60mm**：預設貼紙規格全面鎖定為 `90mm × 60mm`，CSS 列印樣式與版面滿版對齊，杜絕手機瀏覽器邊距干擾。
    3. **LAN 192.168.3.128:9100 原吋直通**：App 內新增 Wi-Fi/Ethernet 印表機直連 Port 9100，1:1 精準停在標籤間隙 (GAP)。
  - **發布與推送**：升級至 `v3.3.6`，更新 Service Worker 快取名稱為 `qc-kanban-v3.3.6-offline`，重新產出 Word 操作手冊，已順利部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 今日進度與交接事項 (2026-11-18 鴻勝化學 QC 看板升級 v3.3.5：TSC LAN 標籤機 90mm×60mm 行動列印支援、RawBT一鍵直印與iPad原吋鎖定)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.5 (`第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **手機與 iPad 列印版面跑位根本問題解決方案**:
    1. **預設貼紙規格鎖定 90mm × 60mm**：系統將標籤機列印設定預設值直接調整為 `90mm × 60mm`，包含寬度、高度、邊界與頁面斷頁，杜絕手機瀏覽器自作主張等比縮放導致的字體忽大忽小與跨頁走位。
    2. **Android 專屬「📱 RawBT 一鍵直印」**：在標籤設定視窗加入一鍵直印按鈕，點擊瞬間自動組裝標準 TSPL 指令（包含單號 Code 128 條碼、品名、槽號、車牌、動向、水分/GC 或 Metal 水平框線手寫欄），以 `rawbt:data...` 協定秒傳給 Android 端 RawBT 服務直送 `192.168.3.128:9100`。
    3. **iPad (iOS) 原吋列印引導**：提供 iPad 直連 `TSC Print Utility` 指南，避免 Safari 預設邊界干擾，1:1 精準停在標籤間隙 (GAP)。
  - **發布與推送**：升級至 `v3.3.5`，更新 Service Worker 快取名稱為 `qc-kanban-v3.3.5-offline`，重新產出 Word 操作手冊，已順利部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 今日進度與交接事項 (2026-11-18 破案與徹底根治：Git for Windows 假成功 Bug 修復、改採 .NET 原生 API 強制終止、升級每小時智慧巡檢排程)
* **Git for Windows 死循環佔用 100% CPU 徹底破案與根除**:
  - **為什麼 11/17、11/18 排程有跑卻依然卡死？（真相破案）**：
    1. **排程確實有準時在 07:30 執行**：查閱 [clean_git.log](file:///d:/GOOGLE%20ANGET/scripts/clean_git.log)，排程器每天 07:30 都有喚醒執行，日誌上也寫了「成功終止 9 個進程」。
    2. **PowerShell `Stop-Process` 假成功陷阱**：原本腳本使用 `Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue`。當 Win32 進程處於 I/O 深度死鎖狀態時，PowerShell 的 `Stop-Process` 會無聲失敗（不拋出例外但進程依然存活）。後續代碼直接寫入「成功終止」，導致日誌產生假成功，那 9 個進程其實從 11/16 一路卡到 11/18，單一進程吃滿 88,000 秒 CPU！
    3. **根因指令抓出**：透過 WMI 抓出卡死進程的 CommandLine 為 `git.exe --no-optional-locks status --porcelain=v2 --branch --untracked-files=all --ignore-submodules=dirty -z`，確認是 IDE（VS Code / Antigravity）Source Control 在超大型目錄下自動觸發遞迴掃描時卡死所致。
  - **解決方案與雙重強化**:
    1. **改採 .NET 原生 API 保證 100% 秒殺**：全面改用 `[System.Diagnostics.Process]::GetProcessById($targetId).Kill()` 與 `WaitForExit(3000)`，實測對 Windows 殭屍進程可達成 100% 徹底滅殺，絕不殘留！
    2. **升級排程為「每天 07:30 起跑 ＋ 每 1 小時自動巡檢」**：
       - 排程任務 `AutoClean_Stuck_Git` 已更新為：每天早上 07:30 起跑，每 60 分鐘自動在背景巡檢一次。
       - 只要抓到運行超過 2 分鐘（正常 git status 僅需 1~2 秒）的死循環進程立即終止，使用者不再需要痛苦忍受整天直到隔天早上！
    3. **實測驗證**：所有累積之卡死進程已全數消滅，CPU 負載直接從 100% 降回 25% 以下正常水位。

---

## 今日進度與交接事項 (2026-11-17 BPM 一般費用報銷單教學影片實務升級：會計審核 5 大建議、個資打碼、ETC 專用章、移除鏡次標記、Lanczos 銳化雙版本輸出)
* **BPM 一般費用報銷單（出差與私車公用）實務教學影片系統全面升級 (`c:\GOOGLE ANGET\blender_3d_demo\build_bpm_sop_video.py`)**:
  - **會計 5 大實務建議完整落實**:
    1. **憑證日期標註**：私車公用 (A05)、高鐵 (A01)、停車費 (A06) 與總清單 (Shot 07)，皆以亮青色框標示右上角「憑證日期」，提醒同仁修改為實際日期。
    2. **聚光燈遮罩與非紅框**：採用背景壓暗聚光燈遮罩 ＋ 琥珀金/晴空青雙層框 ＋ 深藍藥丸標籤，解決原紅框與 BPM 表頭混淆問題。
    3. **高鐵 A01 專屬提醒**：新增提醒卡與字幕，標明高鐵無英文字軌，發票號碼直接填車票上的「13 碼票號」（畫面僅為範例）。
    4. **金額 Key 未稅/含稅原則**：新增金額對照卡，明定 T01（外加 5%）Key 未稅金額、T02（內含 5%）Key 含稅總額、免稅 Key 實付金額，並核對「未稅＋稅額＝含稅」。
    5. **100% 實務導向**：移除 10 秒 3D 動畫，Shot 01 採用行前佐證三寶看板，Shot 08 採用正本交件三步驟流程看板（申請人備齊正本 → 人事核對 → 會計審核入帳）。
  - **個資保護（住家地址馬賽克）**:
    - 在 Google Maps 去程（`fig07`）與回程（`fig08`）路線截圖中，針對「住家詳細地址」進行像素化馬賽克遮蔽。
  - **ETC 官方電子憑證專用章升級**:
    - 全面替換原線上截圖，改為官方 PDF 紀錄列印切圖（含「遠通電收股份有限公司 電子憑證專用章」與扣款 18 元明細），提醒同仁必備專用章。
  - **正式版商業導覽列**:
    - 頂部全面移除「鏡次 0x/08」與進度圓鈕，改為純淨大標題與右側專業標籤「鼎新 BPM 費用報銷教學」。
  - **畫面模糊根治（高清晰銳化演算法）**:
    - 導入 **Lanczos 高階重採樣 ＋ UnsharpMask 智慧文字邊緣銳化 ＋ FFmpeg CRF 17 高保真編碼**，文字表格與數字筆畫清晰立體。
  - **雙版本並行輸出**:
    - ⚡ **1.2x 快速版**（3 分 46 秒，23.3 MB）：`BPM_一般費用報銷單_私車公用教學總片_1.2x.mp4`（預設總片同步指向此版）。
    - 🐢 **正常語速版 (1.0x)**（4 分 30 秒，25.7 MB）：`BPM_一般費用報銷單_私車公用教學總片_正常語速.mp4`。
    - 兩版皆已複製至 `C:\GOOGLE ANGET\` 根目錄，並在 `bpm_storyboard_studio.html` 加入語速版本切換選單。

---

## 今日進度與交接事項 (2026-11-16 Blender 3D AI 自動建模與 FPV 白模運鏡工作室 `blender_3d_demo` 建置、Google Flow 全自動生片鎖定 10 秒 x 1)
* **Blender 5.3 + Blender MCP (`uvx blender-mcp`) + Three.js 3D 數位孿生與 FPV 白模工作室 (`c:\GOOGLE ANGET\blender_3d_demo`)**:
  - **無獨顯筆電輕量化 3D 雙看板 (`index.html` & `fpv_studio.html`)**:
    - 安裝並設定 Blender 5.3、Astral `uv/uvx` 與 `blender_mcp_addon.py`（註冊於 `~/.gemini/config/mcp_config.json`）。
    - 建立 [generate_warehouse_3d.py](file:///c:/GOOGLE%20ANGET/blender_3d_demo/generate_warehouse_3d.py) 自動生成 36 格儲位與巡航 AGV 之 `warehouse_3d.glb`，搭配 [index.html](file:///c:/GOOGLE%20ANGET/blender_3d_demo/index.html) 互動看板。
    - 建立 [generate_fpv_white_model.py](file:///c:/GOOGLE%20ANGET/blender_3d_demo/generate_fpv_white_model.py) 使用 `BLENDER_WORKBENCH` 算圖輸出 5 秒 120 格 `fpv_white_model.mp4`、首尾幀與攝影機軌跡 `fpv_camera_path.json`，搭配 [fpv_studio.html](file:///c:/GOOGLE%20ANGET/blender_3d_demo/fpv_studio.html) 預覽賽博龐克、奇幻武俠、兒童卡通三套首尾幀。
  - **Google Flow 自動上傳與一鍵生成影片 ([auto_upload_flow.py](file:///c:/GOOGLE%20ANGET/blender_3d_demo/auto_upload_flow.py) & [一鍵自動上傳Google_Flow.bat](file:///c:/GOOGLE%20ANGET/blender_3d_demo/%E4%B8%80%E9%8D%B5%E8%87%AA%E5%8B%95%E4%B8%8A%E5%82%B3Google_Flow.bat))**:
    - 支援透過 Playwright CDP (`Port 9222`) 接管本機 Chrome 或於內建瀏覽器自動進入 Google Flow (`https://flow.google.com`)。
    - 自動設定 `設定觸發條件` 為 **`影片 -> 影格 (Frames) · 720p · 10 秒 · x 1`**（透過滑桿步進精準鎖定 `10 秒`、單次生成 `x 1` 僅耗 30 點，不選 `x 2`），自動填入 Prompt 並點擊 **`開始生成`**。
  - **標準四件套與操作手冊**:
    - 已備齊 [README.md](file:///c:/GOOGLE%20ANGET/blender_3d_demo/README.md)、[SKILL.md](file:///c:/GOOGLE%20ANGET/blender_3d_demo/SKILL.md)、[setup_env.ps1](file:///c:/GOOGLE%20ANGET/blender_3d_demo/setup_env.ps1)、[build_manual_doc.py](file:///c:/GOOGLE%20ANGET/blender_3d_demo/build_manual_doc.py) 與 [Blender_3D_AI建模與白模運鏡系統_操作手冊.docx](file:///c:/GOOGLE%20ANGET/blender_3d_demo/Blender_3D_AI%E5%BB%BA%E6%A8%A1%E8%88%87%E7%99%BD%E6%A8%A1%E9%81%8B%E9%8F%A1%E7%B3%BB%E7%B5%B1_%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8A.docx)。

---

## 今日進度與交接事項 (2026-11-16 儲位記錄 PWA 升級 v1.0.20 ~ v1.0.22：人員帳號匯出/匯入、可輸入搜尋品名選單、依品號動態過濾批號)
* **倉儲儲位 PWA 記錄系統 (`儲位記錄\2_PWA_App版` & `儲位記錄\3_Cloudflare_D1版`) 升級至 v1.0.22:**
  - **人員帳號 Excel 匯出與匯入 (`v1.0.20`)**:
    - 在「人員帳號管理（管理員專用）」新增 `📤 匯出帳號`（匯出 `.xlsx` 含帳號、姓名、權限、啟用狀態）與 `📥 匯入帳號`（支援 `.xlsx/.xls/.csv` 批次新增/更新，既有帳號留空保留原密碼、新增帳號留空預設 `1234`）。
    - 後端雲端 [functions/api/[[path]].js](file:///c:/GOOGLE%20ANGET/儲位記錄/3_Cloudflare_D1版/functions/api/%5B%5Bpath%5D%5D.js) 與本機 [run_server.py](file:///c:/GOOGLE%20ANGET/儲位記錄/2_PWA_App版/run_server.py) 均新增 `POST /api/users/import` 端點。
  - **可輸入＋可展開搜尋品名選單 & 依品號過濾批號 (`v1.0.21` → `v1.0.22`)**:
    - 解決原生 `<datalist>` 選定品名後必須刪空才能重選的限制，改為自訂可搜尋下拉選單 `#itemCatalogMenu`（支援打字模糊搜尋品名/品號、輸入自訂新品名、點擊或按 `▾` 直接展開全品項、右側 `✕` 一鍵清除）。
    - 新增 `updateFilteredLots()`，輸入或選取 `品名 / 品號` 時，`#existingLotsList` 與 `#quickLots` 僅顯示該品號/品名目前在倉庫內實際存在的批號。
  - **線上部署**：已部署至 `https://storage-rack-pwa.pages.dev`（`5652b198.storage-rack-pwa.pages.dev`），`sw.js` 快取同步為 `storage-pwa-v1.0.22`。

---

## 今日進度與交接事項 (2026-11-16 儲位記錄 PWA 升級 v1.0.19：修復批次匯入有貨儲位歸零、區域排序錯亂、跨倉庫誤匯鎖定與公司環境 Wrangler 部署修正)
* **倉儲儲位 PWA 記錄系統 (`儲位記錄\2_PWA_App版` & `儲位記錄\3_Cloudflare_D1版`) 升級至 v1.0.19:**
  - **批次匯入有貨儲位顯示 0 筆修復**:
    - **原因**：`崙尾倉儲儲位表.xlsm` 第 1 列大標題含「儲位」兩字導致 `headerRowIdx` 誤判為第 0 列，且 `findCol` 模糊比對誤中 `儲位序號`；另鴻勝 `A01-前` 含中文字導致正規式漏判及合併區域未繼承。
    - **修復**：改為欄位關鍵字評分定位表頭、優先精準比對欄名、支援鴻勝中文儲位代碼與 `lastZone` 繼承，並以真實 `.xlsm` 驗證（崙尾 1,775 筆 / 有貨 577 筆；鴻勝 860 筆 / 有貨 321 筆）。
  - **區域與儲位自然排序修復**:
    - 後端 [functions/api/[[path]].js](file:///c:/GOOGLE%20ANGET/儲位記錄/3_Cloudflare_D1版/functions/api/%5B%5Bpath%5D%5D.js) 與前端 `renderWarehouseData()` 均加入 `localeCompare(..., 'zh-Hant', { numeric: true })`，修正 `1區4層` 排在 `1區1層` 前的問題。
  - **跨倉庫誤匯防呆與版次顯示**:
    - 依儲位/區域格式自動辨識所屬倉庫，若目標倉庫不符則顯示紅色警示 `#importMismatchWarn` 並鎖定匯入按鈕；頂部標題列與登入畫面同步顯示 `v1.0.19`（`sw.js` 快取同步為 `storage-pwa-v1.0.19`）。
  - **公司網路與中文路徑 Wrangler 部署避坑指南**:
    - 公司 SSL 代理環境需設定 `NODE_OPTIONS=--use-system-ca`（Node.js v24）才可正常 `wrangler login` 與呼叫 Cloudflare API。
    - `wrangler` 在含中文目錄（`儲位記錄`）直接編譯 Functions 會發生 `-1073740791` 原生崩潰；已更新 `3_Cloudflare_D1版\一鍵自動部署上雲端.bat`，自動暫存至 `%TEMP%\storage_rack_cf_stage` 純英文路徑部署，並升級全域 `wrangler` 至 `4.162.0`。
  - **線上部署驗證**：已部署至 `https://storage-rack-pwa.pages.dev`（`2d2a4dc4.storage-rack-pwa.pages.dev`），首頁 `v1.0.19` 與 `/api/warehouse/lunwei/data` 均驗證 200 OK。

---

## 今日進度與交接事項 (2026-11-16 鴻勝化學 QC 看板升級 v3.3.4：修復腳本語法錯誤、徹底解決「登入解鎖 (QC放行)」按了沒反應問題)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.4 (`第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **按鈕按了沒反應根本原因查明與修復**:
    - **根本原因**：在上一版替換排程向下相容函數時，函數後方意外殘留了未封裝於 `async function` 內的過渡代碼 `await fetch(...)`，造成瀏覽器解析 `<script>` 時拋出語法錯誤 `Uncaught SyntaxError: await is only valid in async functions`，導致主腳本中斷載入，頂部「🔓 登入解鎖 (QC放行)」及其他全域函式因而點擊無反應。
    - **全面修復**：徹底清除所有非同步孤兒語法，並以 Node.js vm 引擎對全頁所有 `<script>` 區塊進行 100% 語法編譯檢查（Syntax OK），確保所有事件監聽與按鈕點擊完全正常。
  - **發布與推送**：全站升級至 `v3.3.4`，更新 Service Worker 快取名稱為 `qc-kanban-v3.3.4-offline`，重新產出 Word 操作手冊，已順利部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 今日進度與交接事項 (2026-11-16 鴻勝化學 QC 看板升級 v3.3.3：修復無送樣排程卡片渲染、加入 Checkbox 勾選項目與全選/全不選批次清除)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.3 (`第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **清單未顯示問題根因查明與修復**:
    - **根本原因**：在上一版 `renderClearOrdersList` 模板字串中調用了未定義的 `escapeHtml(...)` 工具函數，導致 JavaScript 拋出 ReferenceError 中斷了清單 DOM 的渲染，使得外框呈現空白且僅能看到按鈕。
    - **全面修復**：改以原生字串轉換與安全編碼呈現，經 Node.js 模擬執行與真實 DOM 驗證，清單與 13 筆卡片皆 100% 正常渲染呈現。
  - **全面導入 Checkbox 自由勾選機制**:
    1. **排程項目皆可勾選**：清單中每筆未送樣排程卡片左側加入 Checkbox 核選方塊（預設全部勾選），同仁可隨意勾選要清除的 1 筆、多筆或全部。
    2. **全選 / 全不選快捷鍵**：右上角提供「全選」與「全不選」快捷按鈕，點擊瞬間切換。
    3. **動態動作按鈕連動**：底部按鈕即時動態連動，呈現「清除所勾選的未送樣排程 (已選 X / Y 筆)」，若未勾選任何項目則自動鎖定防呆。
    4. **個別單獨刪除維持保留**：每筆排程右側依舊保留「🗑️ 刪除此筆」按鈕，滿足單筆秒刪需求。
    5. **已送樣排程 100% 防刪安全隔離**：凡是在看板或資料庫已有送樣/檢驗紀錄之排程，持續由智慧保護模組過濾隔離，絕不會出現在清單中，徹底防止誤刪。
  - **發布與推送**：升級至 `v3.3.3`，重新產出操作手冊 Word 檔，已部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 今日進度與交接事項 (2026-11-16 鴻勝化學 QC 看板升級 v3.3.2：排程智慧過濾機制、已送樣100%防刪保護、無送樣單筆與批次刪除)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.2 (`第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **排程清理機制盲點與根本解決方案**:
    1. **原先機制痛點**：舊版「清除槽車排程」視窗僅提供整天或全部清除按鈕，若選定日期內已有同仁「已送樣」或「檢驗判定完成」，該清空操作會將包含已送樣在內的所有排程全數刪除，既不合理也有損壞歷史品管追溯紀錄的風險。
    2. **智慧過濾與已送樣防刪保護**：
       - 利用 `getOrderSubmissionInfo(order)` 智慧比對樣品庫（單號精準比對 + 槽號/車牌/品名/送樣日交叉核對）。
       - 當使用者開啟「清除排程」視窗時，**系統自動將「已送樣 / 檢驗中 / 已判定」之排程 100% 隱藏保護**，上方明確標記「🛡️ 已保護 X 筆已送樣排程」，任何清理指令絕不波及已送樣數據。
    3. **支援單獨刪除無送樣排程**：
       - 清單中**僅動態顯示「無送樣」之待送樣排程**。
       - 每筆排程皆呈現動向徽章、車次時間、單號、品名、槽號、車牌/櫃號與數量，並附帶獨立的「🗑️ 刪除此筆」按鈕，同仁可針對單一取消或重複的排程進行個別刪除。
    4. **一鍵清除選定日期所有【未送樣】排程**：
       - 批次按鈕調整為「🗑️ 一鍵清除選定日期所有【未送樣】排程 (共 Y 筆)」，點擊後僅清除未送樣車次，已送樣車次完整留存。
    5. **後端 API 擴充 (`functions/api/index.js`)**：
       - `clearOrders` / `deleteOrders` 支援傳入 `id`、`doc_no`（單筆刪除）與 `ids` 陣列（批次指定 ID 刪除），達成前後端與 D1 資料庫即時精準同步。
  - **版本更新與正式部署**:
    - 全站升級至 `v3.3.2`，更新 Service Worker 快取名稱為 `qc-kanban-v3.3.2-offline`。
    - 重新編譯操作手冊 Word 檔：`鴻勝化學_QC檢驗即時看板系統_操作手冊.docx`。
    - 順利部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 今日進度與交接事項 (2026-11-16 鴻勝化學 QC 檢驗即時看板 v3.3.1 升級：徹底根治進料單據跳成出貨 Bug、30秒背景輪詢保護、單號特徵嚴格自動對齊與 D1 自癒修復)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.1 (`第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **進料單據跳成出貨根本原因查明與徹底根治**:
    1. **根本原因一（定時輪詢無保護覆蓋）**：系統每 30 秒於背景呼叫 `load()` 取得系統最新配置 `getConfig`，執行 `applyDynamicDropdownOptions` 時直接以 `selFlow.innerHTML = ...` 重新渲染動向下拉選單，因未像 `grade` 一樣保存當前選取值 `curVal`，導致選單瞬間被重設為第一項「出貨」。現場人員若於拉單後等候超過數秒才點擊送出，動向便在背景無聲「跳成出貨」。
    2. **根本原因二（同車多單合併未重新確認動向）**：`openTruckMergeModal` 勾選多單後呼叫 `confirmTruckMerge`，原先僅計算單號與總量，未強制重新鎖定 `flowType`。
    3. **根本原因三（單號特徵缺乏自動推導）**：T100 ERP 中 `ESPM` 開頭必為進料入庫單，`ESXM` 必為出通出貨單。原表單手動貼上或掃描條碼時缺乏對單號前綴的自動動向連動。
  - **全面修復防護措施實裝**:
    1. **`applyDynamicDropdownOptions` 記憶保護**：對 `selFlow` (動向) 與 `selDept` (送樣單位) 全面導入 `curVal` 記憶保存機制，定時輪詢絕不洗掉使用者已選狀態。
    2. **單號前綴嚴格自動對齊 (ESPM = 進料 / ESXM = 出貨)**：
       - `barcode` 輸入框加入即時 `onBarcodeInput`，貼上或輸入 `ESPM` 即秒切「進料」。
       - `applyT100OrderToForm`、`confirmTruckMerge`、`closeTruckMergeModal`、`skipSample` 及前端 `submitForm` 前置過濾全面強制雙重檢驗。
       - 後端 Cloudflare D1 API (`submitSample`) 加入最後防線，凡單號含 `ESPM` 者 100% 強制落庫為「進料」。
    3. **歷史紀錄自癒修復 (`fixFlowTypes`)**：
       - API 成功執行 `UPDATE QC_Samples SET flowType = '進料' WHERE barcode LIKE '%ESPM%' AND flowType != '進料'`，即時將今天許原暢與昨天江承河誤標為出貨的 22 筆 ESPM 單號全數更正為「進料」。
    4. **版本升級與發布**：全站升級至 `v3.3.1`，Service Worker 快取更新為 `qc-kanban-v3.3.1-offline`，已順利部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 今日進度與交接事項 (2026-11-16 系統修復：清除背景死循環 Git for Windows 孤兒進程、CPU 100% 釋放、建置每日 07:30 自動清理排程)
* **Git for Windows 背景程序死循環與 CPU 100% 滿載修復**:
  - **問題根因**：
    1. 工作管理員中累積近 30 個 `Git for Windows` (`git.exe`) 程序，部分程序從 11/13 起已死循環運行超過 83,000 秒（近一天），造成 CPU 100%、記憶體 92% 嚴重卡死。
    2. 主因為 IDE 背景 Git watcher / 超大型目錄索引 / 終端中止後遺留的孤兒進程（Orphaned Process），在 Windows 下未正常結束。
  - **解決方案與防護機制**:
    1. **立即清理**：已強制終止所有殘留孤兒進程，CPU 負載已瞬間從 100% 降回正常（0~5%）。
    2. **每日自動清理排程 (`AutoClean_Stuck_Git`)**：
       - 建立專屬清理腳本 `d:\GOOGLE ANGET\scripts\clean_stuck_git.ps1`。
       - 已註冊 Windows 工作排程器，**設定於每天早上 07:30 準時自動於背景執行**，自動掃描並終止所有背景殘留/超時之 `git.exe`，並一併清除殘留的 `.git/index.lock`。
       - 執行記錄自動記錄至 `d:\GOOGLE ANGET\scripts\clean_git.log`。
    3. **手動一鍵清理工具**：
       - 專案根目錄提供 `d:\GOOGLE ANGET\一鍵清理卡死Git.bat`，平時若察覺電腦異常卡頓，雙擊即可一秒釋放所有 Git 資源。

---

## 今日進度與交接事項 (2026-11-14 LINE 飲食熱量精算師 GAS 系統全面升級：9項完整營養標示、每日累積與建議剩餘對照、文字直接記餐與單項刪改)
* **LINE 飲食熱量精算師 (`C:\GOOGLE ANGET\專案生成工具\generate_docs.py` & `LINE_飲食熱量精算師_Code.gs`)**:
  - **完整 9 項營養標示 + 每日累積 vs 每日建議剩餘/超標**：
    1. 擴充為熱量、蛋白質、脂肪、飽和脂肪、反式脂肪、碳水化合物、糖、膳食纖維、鈉，試算表 `writeToUserSheet` 自動補齊 `G~K` 欄位標題並向下相容舊資料。
    2. 新增 `DAILY_TARGETS`、`getTodayTotals`、`formatDailyProgress` 與 `設定目標` 指令（以 `PropertiesService` 儲存個人化每日目標）。
  - **模型動態偵測與 503 避坑指南**：
    1. **實測發現**：`gemini-3.8-flash`、`gemini-flash-latest` 在尖峰時段偶發 `HTTP 503` 高負載、`2.0-flash` / `2.5-flash-lite` 回傳 `404` 下線，若依序重試多把 Key 會超過 LINE `replyToken` 30 秒效期導致靜默無聲。
    2. **解決方案**：`getDynamicModelPool` 改為 `gemini-2.5-flash` 穩定優先 + `gemini-flash-latest` + 動態最高版備援（快取 6 小時）；遇到 `404` 或 `503` 立即 `break` 換下一模型；加入 45 秒總超時保險，並在 `replyMessage` 加上 `push` 補發機制。
  - **自然語意指令強化**：
    1. 支援直接打食物名稱記帳（如 `鹹酥雞約100公克`）、`新增第X餐 食物`（已存在則追加重算、不存在則建新餐）、`刪除第X餐`（整餐刪除）或 `刪除第X餐的某食物`（只移除單項並重算），以及 `parseMealNumber` 同時支援國字與阿拉伯數字餐號。

## 今日進度與交接事項 (2026-11-14 Wegovy 針劑施打與體重紀錄 PWA 上線、動態劑量規格自訂、時區偏移防呆、Excel 匯出與 Cloudflare Pages 雲端部署)
* **Wegovy 針劑施打與體重紀錄 PWA 系統 (`第一類_核心網頁與互動系統/wegovy-tracker`)**:
  - **核心架構與部署 (`https://wegovy-tracker.pages.dev`)**:
    1. **解決 Google Sites 嵌入沙盒限制**：Google Sites iframe 運行於 `*.googleusercontent.com` 隨機動態子網域且第三方 Cookie / Storage 隔離，導致 `localStorage` 無法跨頁籤持久保存。因此正式獨立部署至 Cloudflare Pages，支援完整 PWA（離線快取、添加到主螢幕如原生 App）。
    2. **標準三件套建立**：完整建立 `README.md`（含詳細檔案架構樹）、`SKILL.md`、`setup_env.ps1` 與 `一鍵部署至Cloudflare.bat`。
  - **功能演進與避坑修復**:
    1. **體重紀錄動態曲線圖表**：整合 Chart.js 動態折線圖，即時監控體重與減重幅度，並提供最新體重、累積減重與施打進度 KPI 看板。
    2. **HTML5 日曆選擇器與 UTC+8 時區防呆**:
       - **避坑指南**：原自動每週推算 (+7天) 使用 `nextDate.toISOString().slice(0, 10)`，在台灣 UTC+8 環境下因午夜轉換被減 8 小時導致日期往前倒退 1 天（例如 11/13 變成 11/12）。改採 `formatDateLocal()` 依本地年月日提取，徹底解決時區偏移問題。
       - **即時響應**：日曆元件同時監聽 `oninput` 與 `onchange`，即使使用者在手機滾輪選完立即點擊推算按鈕，亦能立即獲取最新首週日期。
    3. **Excel (`.xlsx`) 完整匯出功能**：整合 SheetJS（xlsx.full.min.js），一鍵將 6 週施打週次、施打日期、劑量與體重資料匯出為標準 Excel 檔案。
    4. **劑量設定對照支援完全自訂與規格切換**:
       - 支援 1.0mg、1.7mg、2.4mg 預設筆型規格切換。
       - 支援自訂各劑量之名稱、格數與備註，編輯後自動即時同步更新下方每週施打明細的劑量下拉選單。

---

## 前次進度與交接事項 (2026-11-13 倉儲儲位 PWA 記錄系統建置完成：雙倉 .xlsm 無損回寫、儲位平面圖、批號出入庫獨立彙整、人員帳密登入與 Cloudflare D1 雲端部署)
* **倉儲儲位 PWA 記錄系統 (`C:\GOOGLE ANGET\儲位記錄`)**:
  - **三軌架構與標準四件套完整建立**:
    1. `1_Web_網頁版/index.html`、`2_PWA_App版/`（本機區網 FastAPI + PWA）、`3_Cloudflare_D1版/`（Pages + D1 Serverless）。
    2. 完整建立 `README.md`、`SKILL.md`、`setup_env.ps1`、`build_manual_doc.py` 與 `倉儲儲位PWA記錄系統_操作手冊.docx`。
  - **Excel (`.xlsm`) 無損讀寫引擎 (`2_PWA_App版/excel_engine.py`)**:
    1. **避坑指南**：`鴻勝儲位表.xlsm` 的 drawing XML 含有 `pitchFamily > 52`，`openpyxl.load_workbook(..., keep_vba=True)` 寫入會直接報錯且破壞 DataValidation；因此改用 **Surgical XML/ZIP 寫入引擎**，僅修改總表（`崙尾倉儲儲位表_總表202208` / `倉庫總表`）C~H 欄，完整保留 VLOOKUP 公式、VBA 巨集、圖表與 50+ 張分區儲位表連動，寫入前自動備份至 `backups/`。
    2. 新增「下載儲位專用精簡版 Excel（`*_儲位專用.xlsm`）」，自動過濾無關帳卡分頁並重編 `localSheetId`，保留原本儲位表樣式與公式。
  - **核心作業與防呆功能 (`2_PWA_App版/index.html` & `run_server.py`)**:
    1. **儲位卡片顯示**：直接顯示儲位代碼、數量標籤、品名與批號（多批號以 `/` 顯示），並支援品名自動帶出品號與預設包材。
    2. **入庫防呆與多批號支援**：入庫遇已有貨儲位自動彈窗選擇「🔄 覆蓋舊資料（忘記出庫）」或「➕ 併板／累加」；多批號可用逗號分隔，回寫 Excel 自動轉為換行格式（`\n`）。
    3. **總表即時看板與 2D 儲位平面圖**：僅動態顯示架上有貨品名與依備註（`HOLD`/`異常`/`不良`/`後助`/`侯住`）抓取之異常品桶數，並提供全螢幕響應式排版（手機～32 吋螢幕）。
    4. **今日統計與批號核對**：將「📥 今日入庫批號彙整」與「📤 今日出庫批號彙整」分為獨立兩欄（不管儲位依批號加總），並支援匯出 UTF-8 BOM CSV。
    5. **各倉庫獨立品名包材設定（品名可直接修改）** 與 **離線優先自動補傳**（`sw.js` v1.0.12 + `pwa_offline_sync.js`）。
    6. **人員帳密登入與異動追蹤**：預設帳號 `admin` / `1234`（管理員可新增/修改/刪除現場人員）與 `staff1` / `1234`，全螢幕不透明登入頁，每筆異動自動記錄操作人員；`啟動PWA儲位系統.bat` 已轉為 Windows `CRLF` 格式並實測通過。
  - **Cloudflare Pages + 獨立 D1 部署**:
    1. 建立獨立 D1 資料庫 `storage-rack-db`（UUID：`7d562a45-6dd3-43e7-a6c4-d266cfdb22d5`），與原有 `weather-monitor-db`、`qc-db`、`egups-db` 完全隔離。
    2. 已匯入 2,636 筆儲位與品項設定，正式網址：`https://storage-rack-pwa.pages.dev`。

---

## 前次進度與交接事項 (2026-11-12 鴻勝化學 QC 檢驗即時看板 v3.3.0 升級：同車多單彈性配置、重複送樣自主判定防呆、等級智慧動態判定、完成件近2天時區修正與線上部署)
* **鴻勝化學 QC 檢驗即時看板系統升級至 v3.3.0 (`C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版`):**
  - **同車多單合併機制動態彈性配置 (`OPTIONS_MULTI_ORDER_PRODUCTS`)**:
    1. 將多單合併支援品名由寫死代碼改為後台動態自訂，資料庫 `System_Config` 新增 `OPTIONS_MULTI_ORDER_PRODUCTS` 參數（預設 `EBR-P1R, NBAC-P1R, CPN-P1R`）。
    2. 管理後台 `admin.html` 產品總表新增「同車多單合併」獨立勾選欄位，管理員勾選即可生效；非白名單產品（如 GAA、IPA）永遠作為獨立單號直接帶入，絕不誤彈窗打擾。
  - **重複送樣與二次複驗「人員自主判定對話視窗 (`repeatSubmissionModal`)」**:
    1. 當人員點選先前已送樣或已判定之車次時，立即彈出視窗提醒，清楚標註前次送樣時間、送樣人員、完成放行/檢驗中狀態。
    2. 提供「✅ 確定再次送樣 (複驗/重取樣)」與「✕ 取消 (不重複送樣)」兩大按鈕，徹底防止誤登誤送。
    3. 多單合併視窗內已送樣單號解除反灰鎖定，開放人員手動自選合併以滿足二次複驗需求。
  - **產品等級智慧動態判定（取消死板綁定單一等級）**:
    1. 表單 `<select id="grade">` 預設留白提示「-- 系統判定等級 --」，避免重置表單時死板預設。
    2. 採三級判定：後台自訂映射表 > 排程原始指定等級 > 命名特徵精確比對（-P1R/回收 -> 回收液, UPS -> 回收液/UPS, IF -> IF, OEM/電子級 -> 電子級, 標準溶劑品名開頭 -> 工業級）。
  - **已檢驗完成近 2 天展示之 UTC-8 時區偏移修正**:
    1. 原 code 使用 `.toISOString().split('T')[0]` 導致台灣時間上午 07:48 的資料被減 8 小時回退成前一天日期（11/10），進而被近 2 天過濾器刷掉。
    2. 引入 `extractLocalDateStr` 嚴格比對本地年月日，優先比對 `completedAt`，成功修正使 11/11 與 11/12 兩天檢驗完成資料完整正常顯示。
  - **版次統一與文件產出**:
    1. 全站版本統一為 `v3.3.0`，Service Worker 快取升級為 `qc-kanban-v3.3.0-offline`。
    2. 重新產出《鴻勝化學_QC檢驗即時看板系統_操作手冊.docx》(v3.3.0) 與《鴻勝化學_QC檢驗即時看板系統_導入提案書.docx》(五大課室正式版)。
    3. 成功部署至 Cloudflare Pages：`https://qc-samples.pages.dev`。

---

## 前次進度與交接事項 (2026-11-12 勝一三合一單產生系統 PyInstaller 封裝 NumPy C-extension 崩潰修復、熱更新頂部移位與易見 AI 解讀修復)
* **勝一三合一單產生系統執行檔封裝修復與安全導入機制 (`C:\GOOGLE ANGET\勝一三合一單產生系統`):**
  - **NumPy C-extension 崩潰根本原因與修復**:
    1. **崩潰根因**：封裝時為大幅減重排除 `pandas/scipy`，但 `pytesseract` 內部第 35 行預設執行 `from numpy import ndarray`。原 `main.py` 於第 1 行直接 `import pytesseract`，導致 `.exe` 一啟動即拋出 `Importing the numpy C-extensions failed`，甚至來不及執行第 97 行的熱更新即閃退。
    2. **熱更新頂部移位**：將 `_run_cloud_or_local_hot_reload()` 徹底移至 `main.py` 最頂部（僅依賴標準庫 `os, sys, shutil, urllib`），確保在載入任何第三方套件前先完成外部腳本/雲端熱更新判定。
    3. **安全導入與防呆保護**：對 `pytesseract` 實施 `try...except ImportError` 安全包裹，離線 Tesseract 調用時加入 `if pytesseract and Output:` 防禦，杜絕缺少 C-extension 時整支程式癱瘓。
    4. **產出一鍵重新打包工具與完成 EXE 封裝**：新增 `一鍵重新封裝EXE.bat`，內建 12 大基準範本檔 `--add-data` 與自動置換當前目錄 EXE 機制。已重新封裝出 `勝一三合一單產生系統.exe`（74.6 MB）並實測背景啟動驗證成功（PID 23476，無報錯閃退），同步更新 `勝一三合一單產生系統.zip`（73.9 MB）。
    5. **現場人員零安裝 Python 保證**：現場人員解壓縮後直接雙擊 `勝一三合一單產生系統.exe` 即可免裝 Python、免裝依賴套件秒開作業。亦保留 `啟動_勝一三合一單產生器.bat`（執行 `python main.py`）作為雙軌保底。

* **易見｜多重命理分析線上版 AI 截斷與 `undefined` 修復 (`C:\GOOGLE ANGET\第一類_核心網頁與互動系統\yijing-multi-analysis`):**
  - **Groq Token 額度擴增至 3500**：解決原本 1400 tokens 輸出月柱即截斷之嚴重問題。
  - **Prompt 提問直面優先**：新增第一章節直擊提問痛點，並禁用吃大量 token 的大表格。
  - **前端 Markdown 解析升級**：內建表格自動轉換、粗體與大標題解析，徹底修復 `undefined木` 與 `木行 ()` 顯示異常。

---

## 前次進度與交接事項 (2026-11-12 勝一三合一單產生系統 PyInstaller 執行檔封裝與 GitHub 雲端自動熱更新機制實裝)
* **勝一三合一單產生系統執行檔封裝與自動熱更新 (`D:\GOOGLE ANGET\勝一三合一單產生系統`):**
  - **GitHub 雲端自動熱更新 (Hot-Reload) 機制**:
    1. 比照鴻勝版架構，於 `main.py` 頂部植入 `IS_FROZEN`、`RUNTIME_DIR`、`BUNDLE_DIR` 與 `_run_cloud_or_local_hot_reload()`。
    2. 啟動 `.exe` 時自動在 2.5 秒內連線 GitHub 主庫 (`shihwei0809/google-agent` 之 `勝一三合一單產生系統/main.py`) 檢查是否有新版；若有新版則自動下載快取至 `.cloud_cache/main_cloud.py` 並透過 `exec(compile(...))` 無縫熱載入，現場人員免重裝 `.exe` 即可即時獲得最新功能。
    3. 支援三層防呆降級載入：同目錄外部 `main.py` (最新者) ➔ 雲端快取 `.cloud_cache/main_cloud.py` ➔ `.exe` 內建封裝版（斷網環境自動保底執行，絕不報錯當機）。
  - **內建 12 份範本與基準檔「首次自動釋放 + 防覆蓋保護」**:
    1. 將 `台積電槽車barcode三合一單-範本.xlsx`、`地點代號對照表.xlsx`、5 份勝一 `COA.csv` 以及 5 份 `Chemical_Lorry.xlsx` 封裝進 `.exe` 內部。
    2. 首次於空資料夾啟動時自動釋放缺失檔案；若外部目錄已有使用者更新之檔案則嚴格保護不覆蓋。
  - **輕量化單一執行檔與雙軌更新工具產出**:
    1. 排除無關巨型套件 (`torch`, `scipy`, `pandas` 等)，將執行檔由 352 MB 瘦身至 68.4 MB (`勝一三合一單產生系統.exe` 及 `dist\勝一三合一單產生系統-免安裝版.exe`)。
    2. 產出 `一鍵更新系統程式.bat`（支援 Git Pull 與 GitHub Raw 雙軌更新）、`splash.png` 啟動畫面與 `installer.iss` 安裝腳本。

---

## 今日進度與交接事項 (2026-11-11 勝一三合一單產生系統全面重構升級、嚴格批號核對防呆、純欄位名稱動態定位、凍結窗格與自適應介面)
* **勝一三合一單產生系統全面重構升級 (`C:\GOOGLE ANGET\勝一三合一單產生系統`):**
  - **支援勝一 5 大產品最新格式**：
    1. 支援 `CPNE4R` (料號 `L2C9173`)、`SEP73E4` (料號 `L269100`)、`SEP73E5` (料號 `L2C9100`)、`PMAHQ` (料號 `L2C9501`)、`PMAHQ(R)` (料號 `L2R9501`) 之三合一單、COA CSV、單列 `Chemical_Lorry` 生產履歷與運輸通知表。
    2. 更新 `地點代號對照表.xlsx` 完整收錄台積電 41 大槽車廠區指送地（含寶山 `F20P1`、高雄 `F22P1B`、中科 `15BP5A`、南科 `18P7`、先進封裝 `AP7P1`~`AP7P2B`、`AP8` 等），建立短代號、長代號與料號精確對應。
  - **回歸鴻勝三合一嚴格批號核對防呆機制**：
    1. **生產履歷嚴格核對**：載入 `Chemical_Lorry` 時逐筆掃描比對排程批號，有對到顯示 `✅ 批號 ─ 生產履歷已核對到`，沒對到顯示 `❌ 批號 ─ 生產履歷中找不到！(將不會產生此批履歷)`。
    2. **拒絕虛擬偽造**：完全移除先前用範本第 7 列覆寫批號填入的邏輯；只有批號在履歷總表中真實存在時才產出單列 `Chemical_Lorry`，避免填入別批的原料批號與製程數據造成品保重大異常。
    3. **單列履歷原貌輸出**：自動繼承 1~6 列表頭 + 該批第 7 列真實數據，欄寬最適化並將凍結窗格設於 A7。
  - **純欄位名稱動態定位 (Name-Based Dynamic Mapping)**：
    1. 移除死板的預設欄位索引，全面改以表頭文字（如 `出貨通知單單別號`、`批號`、`對象簡稱`、`指送地`、`品名`、`預計到貨日期`、`到貨時間`）進行動態定位。
    2. 不論排程欄位順序未來如何調動，系統皆能自動鎖定正確資料欄位，無須再次修改程式。
  - **使用者介面與操作優化**：
    1. **滿版自動延展 + 下拉時首列固定（凍結窗格）**：主畫面表格支援權重自動伸縮填滿螢幕；頂部標題列凍結於最上方，垂直捲動時標題列永遠對齊可視。
    2. **匯入排程智慧過濾與選取控制**：新增「☑ 全選」與「☐ 全部取消」按鈕（亦可點擊表頭切換全選/取消）；自動過濾排除非排程功能分頁（`barcode`、`coa`、`履歷`、`廠區及產品`），精準只載入有效排程。
  - **程式庫獨立性防呆**：
    1. 本次所有更動嚴格限於 `C:\GOOGLE ANGET\勝一三合一單產生系統`，`C:\GOOGLE ANGET\小包系統報表產生_勝一` 完全未被碰觸（保持原始狀態）。

---

## 今日進度與交接事項 (2026-11-10 ~ 2026-11-11 AI圖片/PDF雙重OCR轉Excel系統建置、跨機自動補裝BAT、三合一單V48雙Key輪詢與配額保護)
* **AI 圖片/PDF 智慧判讀轉 Excel 系統全面重構 (`C:\GOOGLE ANGET\第一類_核心網頁與互動系統\OCR測試\`):**
  - **核心業務功能轉型**：
    1. **手機拍照無損轉正**：透過 `ImageOps.exif_transpose` 自動校正手機陀螺儀方向，徹底解決手機直拍上傳後文字躺臥倒置問題。
    2. **多頁 PDF 逐頁解析**：支援頁次選擇模式（僅第1頁/前3頁/全部/自訂），動態渲染各頁預覽標籤。
    3. **二維表格空間聚類重構**：依文字框高度與 Y 座標聚類為 Row，依 X 座標聚類為 Column，重構為精準二維矩陣。
    4. **商務級 Excel 活頁簿匯出**：自動生成「📋 全部頁面合併總表 / 表格智慧還原」、「📄 各頁獨立分頁」、「📝 辨識明細清單（含綠黃紅置信度條件著色與像素座標）」。
  - **雙重 OCR 引擎架構 (線上 Google Gemini 優先 + 離線 EasyOCR 自動平滑備援)**：
    1. **Google Gemini 2.5 雲端多模態**：具備 API Key 時優先調用，針對繁中、模糊掃描、手寫註記與表格對齊提供最高精準度判讀。
    2. **本機 EasyOCR 備援**：離線、無金鑰或雲端 API 遇 503/配額上限時，系統自動平滑降級為本機 EasyOCR，絕不中斷作業。
    3. **前端網頁整合**：新增金鑰儲存（`localStorage`）與雙重引擎切換卡片，即時標記使用之引擎。
  - **避坑指南與重大錯誤排查修復**：
    1. **OpenPyXL `StyleProxy` 崩潰**：`cell.font` 取值為 `StyleProxy` 不可作為字典鍵，改用單向賦值 `if c not in (3, 4): cell.font = font_data`。
    2. **NumPy `int32` JSON 序列化失敗**：FastAPI 回傳時遇 `np.int32` 拋出 `TypeError: 'numpy.int32' object is not iterable`，加入遞迴清洗函數 `sanitize_numpy()` 與強制原生型別轉換徹底修復。
    3. **Windows CMD 換行字元錯位**：`.bat` 存為 Linux LF 時導致 CMD 指令被截斷執行（出現 `'o'`、`'ul'`、`'_app.py'`），全面轉為嚴格 Windows CRLF (`\r\n`)。
    4. **跨電腦一鍵啟動器升級 (`run_web_app.bat`)**：依照 Rule 8 通用模板，全面支援 Python 環境偵測、pip 自我修復、8 大依賴套件（`fastapi`, `uvicorn`, `easyocr`, `openpyxl`, `Pillow`, `pymupdf`, `google-genai` 等）自動背景補裝、自動 Port 佔用偵測與延遲開窗。

* **三合一單與 COA 雙重核對系統升級至 V48 (`C:\GOOGLE ANGET\第二類_生產管理與API串接\三合一單-to-PHP-Migration\`):**
  - **核對失敗嚴格卡控**：若現場核對未通過，嚴格攔截禁止寫入 Google Sheet 與 Cloudflare D1，且不上傳 R2 與 Drive 照片。
  - **雙 Vision Key 1:1 輪詢與單月硬性 900 次配額保護**：導入 Round-Robin 機制與每月計數器，避免超過 Google 官方每月 1000 次免費額度。
  - **Gemini 3.8 自動降級備援**：全面升級過時之 3.6/3.7 模型，淘汰硬編碼金鑰，全面自 Google Sheet「設定」工作表動態讀取。

---

## 今日進度與交接事項 (2026-11-09 雲端硬碟快照7天嚴格滾動封存修復、三合一單GAS即時無時差同步、排程字體純白樣式修正、易經多重分析系統undefined與維度修正)
* **雲端硬碟收工快照嚴格滾動封存修復 (`AutoSync_OffWork_Drive.ps1`):**
  - **排查修復原因**：原腳本僅依快照數量 `Count > 7` 判斷，逢例假日未開機（如 11/01～11/03）時，即使快照已超過 7 日曆天也不會封存；且原先檢查在今日同步前執行，導致今日快照一寫入，總數又變回 8 個。
  - **雙重卡控機制**：
    1. 條件一（日曆天數）：凡早於 7 天前之快照（`$snapDate < $cutoffDate`，早於 2026/11/01）一律無條件移至 `01_歷史按月封存\YYYY年MM月`。
    2. 條件二（數量上限）：若保留數量已達 7 份，超額之較舊快照亦自動歸檔。
    3. 執行順序調整：改於今日備份同步完成後執行檢查，確保 `00_最近7天收工快照` 內「永遠最多 7 天且最多 7 份快照」。
  - **立即清理成果**：已將 10 月的 4 份超期快照（10/28、10/29、10/30、10/31）全數歸檔至 `01_歷史按月封存\2026年10月`，目前最近7天快照目錄保持乾淨的 4 份（11/04、11/05、11/07、11/08）。

* **三合一單與 COA 核對系統 — GAS 即時雙向無時差同步 (`C:\GOOGLE ANGET\第二類_生產管理與API串接\三合一單-to-PHP-Migration\`):**
  - **建立 Cloudflare 同步 API 接口 (`functions/api/sync-from-gas.js`)**:
    1. 專供 Google Apps Script (GAS) 寫入試算表後即時推送資料至 Cloudflare D1。
    2. 內建防呆去重（同批號＋同時間或同磅單自動跳過）、日期時間字串自動正規化與中文欄位自動轉換。
  - **GAS 即時秒級推送代碼整合 (`Code.gs`)**:
    1. 在 `processFormAndVerify_V10` 將紀錄 `appendRow` 寫入工作表的同一步驟，加入 `UrlFetchApp.fetch` 發送 JSON，現場人員使用 GAS 表單時，Google Sheet 與 Cloudflare D1 毫秒級同步寫入，不受雙月份切換分頁影響。
    2. 補齊 2026-11-08 現場人員使用 GAS 寫入之 3 筆最新合格紀錄（626B07E29J1、626B07E3091、626B06E3181）至 `egups-db.coa_verification_logs`（ID: 224, 225, 226）。

* **ACT / EGUPS 動態生產排程系統歷史存檔字體修正 (`C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統\` | 線上網址: `https://prod-planner-pwa.pages.dev/`):**
  - **字體顏色修復**：排查發現歷史存檔下拉選單動態添加之 class `text-indigo-600 font-bold` 在深色背景下拉中為暗藍色極難辨識，強制修正為純白色（`#ffffff`）粗體，並在全域 CSS 與元素行內樣式加上 `#historySelect, #historySelect option { color: #ffffff !important; background-color: #0f172a !important; }`，徹底根治瀏覽器下拉選單字體對比度問題。
  - **部署配置齊全**：補齊專案根目錄之 `wrangler.toml` 與 `一鍵部署至Cloudflare.bat`，同步支援 `prod-planner-pwa` 與舊網址 `act-planner-pwa`。

* **易見多重命理分析系統全面排查修復與專案收錄 (`C:\GOOGLE ANGET\第一類_核心網頁與互動系統\yijing-multi-analysis\` | 線上網址: `https://yijing-multi-analysis.shihwei0809.workers.dev/`):**
  - **釐清卦象機制**：向使用者說明推演之卦為個人終身「生辰本命卦」（固定依 1982-08-09 丑時數理推算得雷火豐變澤火革），單選按鈕為「分析深度與報告主題」；在卦象區塊新增黃色醒目標籤引導卜卦時點擊「隨機起一卦」。
  - **全面修復多處 `undefined` 錯誤**:
    1. **`元神: undefined木`**：八字排盤計算核心 `calculateFullBazi` 回傳物件漏給 `dayMaster: dayStem` 屬性，導致標籤與文字顯示 undefined，已修正補齊為 `甲木 (身弱)`。
    2. **五行條 `木行 ()` 空括號**：因 `dayMaster` undefined 導致判斷元神失效，修復為僅元神標註 `木行 (本命元神)`，其餘四行保持簡潔無空括號。
    3. **深度維度卡片內容與 AI 提示詞脫鉤**：表單 radio key（`years`, `elements`, `ten`）與底層字典（`comprehensive`, `risk`, `growth`）未對齊，補齊三大維度專屬卡片內容，使選取「深入五行」與「深入十神」時下方卡片即時呈現不同分析面向，並將所選深度注入 AI Prompt。
  - **專案結構標準化**：將原本暫存於 Codex 目錄之專案完整收錄至主庫 `C:\GOOGLE ANGET\第一類_核心網頁與互動系統\yijing-multi-analysis`，建立 `一鍵部署至Cloudflare.bat` 並納入 Git 版控。

---

## 今日進度與交接事項 (2026-11-08 三合一單與COA核對系統V46轉移至Cloudflare+R2+PWA雙邊同步架構、三大核心D1資料庫整併完成、歷史222筆全數同步)
* **台積三合一單與COA雙重核對系統 V46 (`C:\GOOGLE ANGET\第二類_生產管理與API串接\三合一單-to-PHP-Migration\` | 線上網址: `https://coa-check-pwa.pages.dev/`):**
  - **雙軌架構正式發布 (Cloudflare Pages + Functions + D1 + R2 + PWA)**:
    1. **前端雙軌離線防呆 (V46)**：連線時使用 Google Vision API，斷網時改用手機晶片離線 OCR（Tesseract.js）。
    2. **嚴格現場卡控**：若現場核對「失敗」，即時亮紅燈警報攔截，**絕不上傳、絕不寫入暫存**；若核對「合格且斷網」，資料自動存入手機離線合格隊列，**一旦偵測到網路恢復，背景自動補傳**至 Cloudflare D1、R2 照片庫與 Google 試算表。
    3. **雙邊寫入機制**：動態向既有 GAS Web App 索取金鑰與 Teams Webhook，資料核對合格後同時寫入 Cloudflare D1 與 Google 試算表對應的雙月份分頁（如 `Data_2026_11-12`），照片連結存為 R2 高畫質直連網址，零耗損 Google Drive 容量。
    4. **查詢頁雙軌響應式升級與狀態防呆修正 (`query.html`)**:
       - **錯誤排查修復**：排除前次比對硬性要求 `四重核對成功` 導致所有 `核對成功` 歷史紀錄誤判為紅字 `❌ 核對失敗` 之 Bug，改為智慧包含相符。
       - **手機卡片流 (Card View) + 桌機表格 (Table View)**：手機自動渲染大字藍色批號卡片與綠燈狀態標籤，桌機顯示完整寬表格。
       - **日期快捷快篩晶片**：支援 `近 3 天`、`今天`、`昨天`、`近 7 天`、`全部` 與 `自訂區間`。
       - **相片預覽智慧分流**：Google Drive 連結支援在新分頁開啟原圖，Cloudflare R2 支援高畫質彈跳燈箱預覽。
    5. **Google 試算表 9、10、11 月完整資料導入 (共 222 筆)**：
       - 透過 GAS Web App API 完整撈取 2026-09-01 至 2026-11-07 歷史核對紀錄，全數寫入 `egups-db.coa_verification_logs`，並重設資料庫 ID 排序。
* **Cloudflare D1 資料庫整併大行動 (9 庫 ➔ 3 大核心庫，釋出 7 個可用額度)**:
  - 依照三大核心資料庫規劃，完成逐一遷移與防呆刪除：
    1. `coa-check-db` ➔ 結構遷入 `egups-db.coa_verification_logs`，已刪除。
    2. `tsmc-verification-db` ➔ 42 筆歷史資料遷入 `egups-db.coa_verification_logs`，已刪除。
    3. `nitrogen_valve_records` ➔ 遷入 `training-db` 與 `egups-db`，已刪除。
    4. `chemflow_pro_db` ➔ `flow_data` 遷入 `egups-db`，已刪除。
    5. `ipa-pwa-db` ➔ `ipa_data` (8筆) 與 `ipa_archives` (5筆) 遷入 `qc-db`，更新其 `wrangler.toml` 並推送 GitHub，已刪除。
    6. `training-db` ➔ `materials` 與 `chat_logs` 遷入 `weather-monitor-db`，更新其 `wrangler.toml` 並推送 GitHub，已刪除。
  - **目前 Cloudflare D1 僅保留三大核心資料庫 (名額剩餘 7 個)**:
    1. 🏭 **`egups-db`** (`b87a145c-937d-430b-94f0-1962255abd04`): 生產管理、進耗存、回收液、三合一單與 COA 核對。
    2. 🧪 **`qc-db`** (`a4cbfe74-f067-462b-b70a-be242f9fafb9`): 品管化驗、樣品管理、IPA 生產排程與進耗存。
    3. 🌤️ **`weather-monitor-db`** (`521c2592-1953-42a3-a559-bd403c8d3017`): 廠務氣象監控、高低溫通報、員工教育訓練題庫與問答。

---

## 今日進度與交接事項 (2026-11-07 永豐金證券 Shioaji 即時看盤儀表板專案建置、雙軌實盤/模擬盤架構、Windows CMD Big5 編碼防呆修復)
* **永豐 Shioaji 即時看盤儀表板 (`C:\GOOGLE ANGET\shioaji-market-dashboard\` | 本機服務位址: `http://localhost:8088`):**
  - **完成專案核心後端與雙軌行情引擎 (`server.py`)**:
    1. 整合 FastAPI、WebSockets 與幾何布朗運動高仿真模擬撮合引擎，支援台積電 (2330)、鴻海 (2317)、聯發科 (2454)、元大台灣50 (0050)、台指期 (TXF) 等標的秒級跳動 K 線、動態五檔撮合與逐筆成交。
    2. 支援直連永豐金證券官方 Shioaji API，金鑰 100% 留存在本地端，零雲端外洩風險，徹底解決 Colab 閒置斷線與金鑰資安問題。
    3. 實作智慧 Port 佔用偵測自動切換 (Port Fallback) 與區域網路 IP 抓取，以及自動延遲彈出瀏覽器看盤頁面。
  - **專業級三欄 TradingView 看盤介面 (`static/` | `index.html`, `style.css`, `app.js`)**:
    1. 引入 TradingView Lightweight Charts 4.x，實作台股習慣「漲紅跌綠」秒級 K 線、成交量副圖、分時折線切換。
    2. 最佳五檔委託深度 (Order Depth-5)：實作紅買綠賣動態長條圖百分比視覺化。
    3. 逐筆明細流水帳 (Tick Tape)：毫秒級流水帳，自動判定外盤主動買與內盤主動賣，具備平滑淡入動畫。
    4. 支援觀察清單 (Watchlist) 即時輪巡報價更新、自訂代號搜尋訂閱，以及系統設定彈窗切換實盤與模擬盤。
  - **專案標準規範文件與自動生成器完整建置**:
    1. `README.md` (人類說明書，含完整目錄樹與啟動流程)。
    2. `SKILL.md` (AI 代理指導規範)。
    3. `setup_env.ps1` (一鍵 PowerShell 自動安裝腳本)。
    4. `build_manual_doc.py` (Word 操作手冊自動產出腳本)。
    5. `.env` 與 `.env.example` (環境變數設定範本)。
  - **Windows CMD Big5 (CP950) 踩坑防呆與修復指南**:
    1. **錯誤現象 1**: BAT 腳本解析 `pkg|pkg>=version` 時，CMD 誤判為管線與重定向，將套件名稱當作指令執行，導致跳出 `'pydantic' 不是內部或外部命令` 並中斷跳至 Python 下載頁。
    2. **錯誤現象 2**: Python 輸出含有 Unicode 符號（如 `\u26a1` ⚡ 與 `\ud83d\udca1` 💡）時，在 Windows 預設 CP950 控制台會觸發 `UnicodeEncodeError: 'cp950' codec can't encode character` 崩潰。
    3. **錯誤現象 3**: `.bat` 檔若為 UTF-8 且含中文註解，Windows CMD 在 Big5 解碼下會因多字節錯位將指令截斷（如 `echo.` 變 `'ho.' 不是內部或外部命令`）。
    4. **正確解決方案**: 
       - `.bat` 檔一律採用純 ASCII 英文指令（`啟動看盤儀表板.bat`）。
       - Python `server.py` 最頂層加入 `sys.stdout.reconfigure(encoding="utf-8")`，並全面將主控台輸出換為相容性純文字。

---

## 進度與交接事項 (2026-11-05 IPA 與 ACT/EGUPS 動態排程系統全功能升級與發布)
  - **歷史存檔改名與直接覆蓋更新**: 兩大系統（IPA 與 ACT/EGUPS）之歷史存檔區全面升級，新增 ✏️ 改名 與 🔄 覆蓋 功能，並將原存檔按鈕調整為 ➕ 另存新檔。覆蓋時直接原地更新 LocalStorage 與雲端資料庫（IPA D1 / ACT Google Sheet），不需再重複新增多筆記錄。
* **IPA 生產排程與進耗存整合系統 (C:\GOOGLE ANGET\IPA 專用動態生產排程與進耗存整合系統 | 線上網址: https://ipa-pwa-app.pages.dev):**
  - **日報數據解析修復**: 修正 08:00 儲槽報表零值防呆，避免 16:00 數據回填滲漏導致 11/5 一廠總重誤判為 230.71T（正確為 217.32T）。
  - **真實槽位數值套用**: 首日個別儲槽改為依據作業日報真實數值填入，不再採平均分配。
  - **歷史封存刪除功能**: 比照主系統新增管理員密碼驗證（8888），支援從 Cloudflare D1 雲端資料庫刪除歷史排程紀錄。
  - **高質感彩色公式 Excel 匯出**: 引入 ExcelJS，產出含石板灰表頭、紅底週末、雙區塊配色與全自動公式連結之 .xlsx 活頁簿。
  - **版次升級**: 介面版次正式標記為 4.0，並推送到 origin main。

* **ACT / EGUPS 動態生產排程與進耗存整合系統 (C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統 | 線上網址: https://prod-planner-pwa.pages.dev):**
  - **彩色公式 Excel 匯出升級**: 比照 IPA 系統重構 exportToExcel()，匯出 Sheet 1（動態進耗存表）與 Sheet 2（槽車出車動態排程），支援即時計算公式與安全警戒上色。
  - **離線 PWA 支援**: 本地封裝 exceljs.min.js，更新 sw.js 快取名單並推進快取版本至 ct-pwa-v2.1。
  - **Cloudflare Direct Upload 部署修復**: 排查確認此專案在 Cloudflare Pages 為 Direct Upload 模式（無 Git 連線 Webhook），需透過 Wrangler 部署。針對 Node 24 環境升級採用 wrangler@4.158.0，成功將最新版發布至 prod-planner-pwa.pages.dev 與舊相容網址 ct-planner-pwa.pages.dev。
  - **一鍵部署腳本同步**: 更新 一鍵部署至Cloudflare.bat 為 wrangler@4.158.0，確保日後雙擊亦可一鍵部署。

---

## 今日進度與交接事項 (2026-11-04 易見｜多重命理分析網站升級與三軌 AI 整合部署、跨網遠端桌面防火牆穿透檢測)
* **易見｜多重命理分析網站 (`C:\Users\C606\Documents\Codex\2026-11-02\new-chat\outputs\yijing-online-site\` | 線上網址：`https://yijing-multi-analysis.shihwei0809.workers.dev`):**
  - **依《易見網站建置說明書_AGY.md》完成全規格資訊架構重構**:
    1. 全面升級視覺與六大區塊（Hero 區塊、金色框線隱私與免責提示、雙欄響應式表單、互動分析結果三卡片與深度分析面板、視覺化六爻起卦區、FAQ 與頁尾）。
    2. 實作集中式 `YIJING_CONFIG` 設定物件，支援 4 種收入、5 種投資、4 種資產目標、3 種風險承受度、3 種研究方向、3 種分析深度之全單選切換與即時重算。
    3. 內建 `@media print` 列印／另存 PDF 專屬排版，並將表單預設值全面去個人化（改為 `1990-01-01`、`午時`、出生地空白、性別不指定）。
  - **整合三軌混合 AI 深度綜合解讀（Groq 內建高速引擎 + Cloudflare Workers AI + 選填自備 Gemini Key）**:
    1. 透過 `wrangler secret put GROQ_API_KEY` 將金鑰安全存入 Cloudflare 雲端加密環境變數（前端與原始碼零金鑰外洩）。
    2. 後端 `/api/ai-insight` 預設優先呼叫內建 Groq 高速模型，並以 Cloudflare Workers AI (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`) 作為自動備援；前端亦支援選填個人 Gemini API Key 直連（含 `3.8-flash` 至 `1.5-flash` 自動降級）。
    3. 嚴格執行去識別化保護：AI 提示詞僅傳送干支五行象意、時辰、財務情境與提問，絕不傳送西元出生年月日與出生地。
* **跨網遠端桌面與公司防火牆穿透診斷 (`C606-NB` ➔ `C606-PC1`):**
  - 排除大陸製 ToDesk 強制 `+86` 手機實名制與資安疑慮，實測確認美國開源免註冊之 **HopToDesk (`https://www.hoptodesk.com`)** 與歐洲開源純 HTTPS 之 **DWService (`https://www.dwservice.net`)** 可直接通過公司防火牆（HTTP 200），免連公司 VPN 即可跨網遠端連線。

## 今日進度與交接事項 (2026-11-04 小包系統報表產生_勝一：五大生產履歷結構與差異分析、同日多筆續寫、CPN雙料號/雙槽號判別、SEP73雙原料保護與舊版.xls相容)
* **小包系統報表產生_勝一 (C:\GOOGLE ANGET\小包系統報表產生_勝一\):**
  - **完成五大生產履歷 (PR) 結構整合分析與產出分析 Excel 報表 (五大生產履歷結構與差異分析整合表.xlsx)**:
    1. 深入分析新加入的 4 份生產履歷 (L2C9170 CPN、L2C9180 PMAUPS、L269000 SEP73E4、L2R9500 PMAHQ(R)) 與原 L2C9172 CPN 之欄位結構差異。
    2. 自動產出高質感對比活頁簿，包含主分頁「📊 整合差異分析」及各檔案獨立分頁，清楚標記第 8 欄 (Col H) 起的分歧點。
  - **生產履歷架構原則確立：1~6 列為模版固定層，第 7 列之後為排程填寫層**:
    1. 第 1~6 列 100% 保持模版原值與表頭不動。
    2. 同一天同廠區若有 2 筆以上排程，第 1 筆寫入第 7 列、第 2 筆寫入第 8 列、第 3 筆寫入第 9 列... 依此類推往下續寫，並完整複製第 7 列之格式、框線與固定槽號。
  - **同品名 CPN 雙料號 (L2C9172 vs L2C9170) 與雙槽號 (TK641 vs TK644) 智慧判別**:
    1. 實作 deduce_cpn_tank_and_mat，依排程品名 + 批號中的槽號特徵代碼（如 K41 ➔ TK641 對應 L2C9172；K44 ➔ TK644 對應 L2C9170）自動精準選擇模版並將對應槽號填入 Tank No.。
  - **PMAHQ 新液 (L2C9500 / M01 / MT5801) 與 PMAHQ(R) 回收液 (L2R9500 / M02 / MT5802) 槽號推導**:
    1. 依批號特徵嚴格分流：M01 ➔ 綁定 L2C9500 新鮮液模版，自動推導 Mixing Tank No. 為 MT5801。
    2. M02（或品名含 (R)、規格含回收）➔ 綁定 L2R9500 回收液模版，自動推導 Mixing Tank No. 為 MT5802。。
  - **SEP73E4 雙原料批號防呆與原料留白原則**:
    1. 因 SEP73 包含 PGME 與 PGMEA 雙原料，出貨排程僅有單一欄位，系統一律不自動填寫原料批號，保留空白交由現場人員手動確認填寫。
    2. 其他單原料品項排程有值時才填入，排程留白則維持空白。
  - **舊版 .xls (BIFF8) 支援與多桶逐桶保護**:
    1. 內建純 Python BIFF8 讀取引擎，無縫載入舊版 Excel 並自動以標準 .xlsx 產出。
    2. 現成多桶檔案（如 32 桶之 L2R9500）同步更新所有資料列，完全保護現有桶號與工單時間不被沖掉。



## 今日進度與交接事項 (2026-10-31 動態生產排程系統全面更名 prod-planner-pwa、網址動態同步、LINE分享卡片優化、試算表唯一資料庫對齊與密碼保護刪除存檔)

* **動態生產排程與進耗存整合系統 (`C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統\`):**

  - **正式部署全新中立主要網址與雙軌無縫銜接 (`prod-planner-pwa.pages.dev`)**:

    1. 解決原網址 `act-planner-pwa` 造成人員誤會為單一產品問題，建立並發布全新專案 `https://prod-planner-pwa.pages.dev/`。

    2. 舊網址 `https://act-planner-pwa.pages.dev/` 同步發布並內建自動銜接跳轉邏輯，原有書籤與通訊軟體舊紀錄完全不失效，點開即自動平滑遷移至新網址。

  - **網址參數動態同步與指定產品直連 (`?prod=產品名`)**:

    1. 實作 `window.history.replaceState` 動態參數同步：在介面切換產品時，網址列即時變更為 `?prod=EGUPS` 或 `?prod=ACT`。

    2. 支援指定產品直連開頁（如傳給人員 `https://prod-planner-pwa.pages.dev/?prod=EGUPS`，點開直接鎖定 EGUPS），並支援瀏覽器上一頁/下一頁返回按鈕。

  - **根治 LINE / 通訊軟體分享卡片預覽 (Open Graph Meta 標籤)**:

    1. 於 `index.html` 頂部加入 `og:title`、`og:description`、`og:type` 與中立的 `<title>`，解決通訊軟體爬蟲抓取死板 ACT 舊抬頭問題。

  - **歷史存檔「以 Google 試算表為唯一準則」同步修復**:

    1. 釐清系統無 Cloudflare DB，唯一雲端資料庫即為 Google 試算表 `ArchiveStore`。

    2. 修復前端 `fetchCloudArchives` 原先只增不減的缺陷，改為先清除本地屬於該產品之舊快取，100% 以 Google 試算表當前存檔列為準。

  - **線上密碼保護刪除存檔功能 (`deleteHistoryRecord`)**:

    1. 前端新增紅色「🗑️ 刪除」按鈕，內建管理員密碼驗證（預設 `8888` / `admin`），杜絕人員誤觸誤刪。

    2. 本地快取立即清除，並同步呼叫 Google Apps Script `action: "delete_archive"` 實體刪除試算表對應列。

  - **GAS 原生 HTML 與 Cloudflare 雙軌運行架構支援**:

    1. 釐清 GAS Web App 點開呈現 JSON 之原由（`doGet` 原僅提供健康檢查 API），升級 `doGet` 支援 `HtmlService.createHtmlOutputFromFile('index')`，使 Google Apps Script 網址亦可直接作為圖形介面使用。

    2. 確立 GAS 內部 HTML 與 Cloudflare Pages 為完全獨立之雙軌備援架構，GAS 端更新與 Cloudflare 前端互不干擾，維持 100% 穩定。



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







## 前次進度與交接事項 (2026-11-09 收工)
* **功能優化與修復 (IPA 專用動態生產排程與進耗存整合系統 - PWA 版):**
  - **共用池預估表小數點顯示**：將「彰濱一廠共用原料池合計總量預估表」中 5 大核心指標（共用池總期初量、製程耗用原料總量、共用池調撥、共用池進貨、共用池當日剩餘結存）從整數顯示升級為保留小數點後 1 位 (`.toFixed(1)`)。
  - **匯出格式同步**：ExcelJS 匯出數字格式修正為 `#,##0.0`，CSV 匯出資料亦全面對齊小數 1 位。
  - **Cloudflare Pages 部署**：完成線上重新編譯並熱部署至 `https://ipa-pwa-app.pages.dev`。
* **功能修復 (易經多重命盤與財務策略報告系統):**
  - 修復八字與易經排盤報告中五行、日主元神與起卦相關欄位 undefined 顯示異常與卦象一致性問題。
* **腳本維護 (AutoSync_OffWork_Drive.ps1):**
  - 修正收工備份保留機制，確保超過 7 天之收工備份正常進行封存移轉。

## 前次進度與交接事項 (2026-11-11 收工)
* **功能修復 (ACT 動態生產排程與進耗存整合系統 - prod-planner-pwa.pages.dev):**
  - **歷史存檔選單文字顏色修正**：排查現場反應歷史紀錄文字為藍色在暗色背景難以辨識問題，將 `<select>` 及 `<option>` 文字顏色統一改為白色 (`#ffffff`)，快取推進至 `act-pwa-v2.3` 並重新部署。
* **架構升級與問題排除 (鴻勝化學 QC 樣品即時管理系統 - qc-samples.pages.dev):**
  - **超時未通知根本原因排查**：分析現場樣品滿 6.1 小時才通知之原因，確認原系統僅於前端開啟時由瀏覽器觸發超時檢查，若無人開頁面則無法送出警報。
  - **24/7 背景排程 Worker 建立與部署**：於 Cloudflare 部署獨立 Worker (`qc-overdue-cron`)，設定原生 Cron Trigger 每 5 分鐘自動呼叫一次 `checkOverdue` API，徹底脫離瀏覽器開關限制，實現 24/7/365 全天候超時警報自動推送至 Teams。
  - **防重複發送驗證**：確認單一超時事件依資料庫 `isAlerted` 狀態嚴格限制最多發送 2 次（滿 2 小時、滿 4 小時），完成判定後立即排除。
* **功能升級 (IPA 專用動態生產排程與進耗存整合系統 - ipa-pwa-app.pages.dev):**
  - **共用池預估表支援直接編輯**：將「彰濱一廠共用原料池合計總量預估表」中的【共用池調撥 (+)】與【共用池進貨 (+)】開放為可直接輸入框。
  - **自動歸入 TK604A**：修改總表數值時，差額預設自動調整至一廠主力儲槽 `TK604A`，並與各槽底層資料、結存剩餘量即時同步。
  - **版本更新與部署**：系統升級至 `v4.2 (快取 ipa-pwa-v4.2)`，完成 Cloudflare Pages 熱部署。



## 前次進度與交接事項 (2026-11-16 收工)
* **問題排查與體驗優化 (IPA 專用動態生產排程與進耗存整合系統 - ipa-pwa-app.pages.dev):**
  - **狀態燈號誤解排查**：現場反映網頁疑遭公司防火牆阻擋，經排查確認網頁各項指標與排程計算均正常渲染，但右上角狀態標籤因待機時預設文字為 `○ 連線中`，容易導致使用者誤以為連線卡死或被公司阻擋。
  - **狀態燈號全面升級**：將閒置待機狀態改為清晰安心的翡翠綠恆亮燈號 **`● 系統就緒`**；儲存時顯示 `○ 儲存中...`，儲存成功顯示 `● 儲存完成`，2 秒後平穩切回 `● 系統就緒`。
  - **PWA 版本推進與熱部署**：推進版本至 `v4.3.1 (系統就緒燈號優化版)`，快取推進至 `ipa-pwa-v4.3.1`，完成 Cloudflare Pages 熱部署。
* **架構升級與功能完善 (倉儲儲位 PWA 記錄系統 - storage-rack-pwa.pages.dev):**
  - **登入驗證確認**：確認預設管理員帳號為 `admin`、密碼為 `1234`（共 4 碼數字），現場人員為 `staff1` / `1234`。
  - **Excel 下載 404 與分頁遺失根本原因排查**：排查雲端 D1 版缺少 `/api/warehouse/{whId}/download` 路由之問題，並修正先前臨時前端產出導致 50+ 張分區儲位平面圖分頁遺失之缺失。透過專案核心 Surgical 引擎還原生成 `崙尾倉儲儲位表_儲位專用.xlsm`（40 個分頁）與 `鴻勝儲位表_儲位專用.xlsm`（26 個分頁），完整保留各區平面圖與公式連動。
  - **新增一鍵匯入更新 Excel/CSV 功能**：解決測試期現場人員在傳統 Excel 登打導致正式切換時的重工痛點。前端智慧支援 `.xlsm`（自動辨識總表分頁）、`.xlsx`、`.csv`，並具備預覽核對面板與即時寫入進度條（0%~100%），分批寫入 D1 資料庫後自動刷新看板。
  - **PWA 快取推進與熱部署**：快取升級至 `storage-pwa-v1.0.16`，完成 Cloudflare Pages 正式熱部署上線。
