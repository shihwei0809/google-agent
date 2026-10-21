# 跨電腦交接日誌 (HANDOVER)

## 今日進度與交接事項 (2026-10-21 槽車與物流商評鑑稽核系統建立、雲端硬碟快照滾動封存機制修復)
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

* **避坑指南 (Cross-Device Pitfalls):**
  - **Google Drive 雲端同步虛擬盤延遲**: G 槽為 Google Drive 串流虛擬磁碟，執行大規模檔案搬移時，避免多個 robocopy 或 PowerShell 同時存取同一路徑，改以循序判斷移動最為穩健。
  - **二進位評鑑與分析表管理**: 新生成的 `.xlsx` 檔案必須以 `git add -f` 強制納管，避免受 `.gitignore` 阻擋而遺失於跨機環境。


## 今日進度與交接事項 (2026-10-20 教育訓練教材全面升級 Cloudflare PWA 邊緣版、串接 R2 物件儲存與 D1 無伺服器資料庫)
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
  - **避坑指南 (Cross-Device Pitfalls)**:
    1. **Pages 嚴禁 account_id**: Pages 專案的 wrangler.toml 嚴禁寫入 account_id 欄位（Pages 會自動綁定），否則會觸發 Configuration file for Pages projects does not support 'account_id' 錯誤。
    2. **R2 CLI 必須帶 --remote**: 使用 wrangler r2 object put 同步雲端檔案時必須帶 --remote 參數，否則預設只寫入本機模擬器。
    3. **批次檔必須純 ASCII + CRLF**: Windows .bat 檔內若含中文字串且使用 LF 換行，cmd.exe 會發生字節位移並吃掉指令關鍵字，必須改用純 ASCII 配合標準 CRLF 換行。
    4. **Pages 專案需先建立後部署**: 首次部署若尚未建立專案，應以 wrangler pages project create <name> --production-branch=main 建立後再執行 wrangler pages deploy。

## 今日進度與交接事項 (2026-10-20 中央大腦納管大型 Git 倉庫雙機通用（桌機與筆電一律適用）防狂搜與 CPU 降載全域標準)
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
