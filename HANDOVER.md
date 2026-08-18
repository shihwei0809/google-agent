# 🔄 跨電腦交接與防呆日誌 (HANDOVER)

**目的**：記錄跨電腦開發的狀態、發生過的嚴重錯誤與避坑指南。AI 助理在「開工」時必須優先閱讀此檔案，以避免踩雷或引發無限錯誤迴圈。

---

## 📅 最新交接紀錄 (2026-08-18)

### 📌 全域專案操作手冊盤點與補齊 (Word & PDF)
* **完成功能**：
  1. **三合一單與運輸通知表自動產生器**：產出 `三合一單與運輸通知表自動產生器_操作手冊.docx` 與 `.pdf`。
  2. **AI 面試語音特質與資材適性分析系統 (interview_analyzer)**：補齊產出 `AI面試語音特質與資材適性分析系統_操作手冊.docx` 與 `.pdf`。
  3. **溫度通報系統**：補齊產出 `溫度通報系統操作說明.pdf` (完成 Word + PDF 雙備份)。
  4. **同檔併排「出貨排程修正通知」卡片**：在 `運輸通知表.xlsx` 同一分頁右側（H~M 欄）自動併排生成「出貨排程修正通知」卡片。
  5. **當天日期資料夾資料歸檔**：產出的檔案統一歸檔至 `三合一單輸出_YYYYMMDD` (如 `三合一單輸出_20260818`)。
  6. **三合一單 Excel 檔名規格重構**：更新檔名格式為 `[出貨日期]. [地點]台積電槽車barcode三合一單.xlsx` (例：`2026.8.18. 18P3B台積電槽車barcode三合一單.xlsx`)。
* **避坑與修復日誌**：
  - 全域掃描所有子專案，確認手冊均改採人員通用的 Word (`.docx`) 與 PDF (`.pdf`) 雙格式，避免僅存 `.md` 檔導致人員無法開啟閱讀。

---

## 📅 最新交接紀錄 (2026-08-17)

### 📌 AI 面試與職缺需求分析系統 (interview_analyzer) 升級與防呆
* **完成功能**：
  - **4 大分頁 Excel 試算表結構**：將 `職缺需求與部門清單.xlsx` 重構為：
    1. `彰濱廠區職缺清單` (9 個實體刊登職缺全數精準到位)。
    2. `勝一總公司(高雄)職缺清單` (18 個實體刊登職缺全數精準到位)。
    3. `AI建議參考職缺與規格擬定` (完整保留原本 AI 大腦擬定的 8 大範本職缺供人資對照參考)。
    4. `DISC 人格類型參考說明` (DISC 特質定義與適合職務參考)。
  - **修復 404 下載與爬蟲按鈕**：新增 `/api/download-job-specs-excel` 點擊一鍵下載路由，並修復前端 `trigger104Crawler()` 連線 104 自動爬蟲與彈窗提示。
  - **自動清理職缺名稱前綴**：實作 `clean_job_title()` 自動將 `【彰濱廠區】`、`【高雄廠】` 等括號字樣濾除，統一呈現純職務名稱。
* **避坑與修復日誌**：
  - **解決爬蟲過度去重誤殺**：原本使用模糊子字串比對 (`ex in t or t in ex`)，導致已有「助理工程師」時「品管助理工程師」與「品保工程師」被誤殺。已修復為精準完全相等比對 (`t in existing_exact_titles`)。
  - **解決自動防重複收工**：於主動收工流程中註記當日紀錄，確保隔天開機時不會觸發二次自動收工。

---

## 📅 最新交接紀錄 (2026-08-14)

### 📌 三合一單自動產生器 (Tkinter GUI 開發與防呆優化)
* **功能完成**：
  - 開發 `三合一單自動產生器` (Python + openpyxl + Tkinter)，支援自動寫入槽號、批號、地點並產生多份 Excel。
  - 整合 `qrcode` 與 `Pillow` 套件，能夠根據範本內容與寫入值自動重新產生並覆蓋舊的 QR Code 圖片。
  - 實作智慧黏貼 (`<<Paste>>`)，使用者可從 Excel 複製多筆資料（支援批號與地點多欄，或單獨一欄），程式會自動分割 Tab 並填入對應欄位，且自動從 10 碼批號中擷取 3~4 碼的槽號。
  - 在地點後方即時顯示長代號，並加入嚴格防呆（若地點不在對照表內，立即報錯並阻擋產生）。
* **解決錯誤**：
  - 解決新舊範本不相容導致 `MergedCell is read-only` 錯誤：改用動態搜尋 B 欄標籤（'槽號', '批號' 等），而非寫死座標。
  - 解決單欄貼上時 Tkinter 預設貼上導致所有資料擠在同一格的問題：綁定全域 `<<Paste>>` 事件並回傳 `"break"` 攔截預設行為，並偵測游標所在的 `target_col` 來精準分配單欄貼上的內容。
* **接手指示**：執行 `C:\GOOGLE ANGET\三合一單自動產生器\啟動_三合一單產生器.bat` 即可啟動（會自動安裝依賴）。

---

## 📅 最新交接紀錄 (2026-08-08)

### 📌 專案路徑歸位與整合
* **狀況描述**：先前開發時將「互動式網站」程式碼存放在 `C:\GOOGLE ANGET\interactive-web-training`，但這不符合本機的專案管理與雙庫防呆大廳規則。
* **解決方式**：已將所有 Level 1 到 Level 5、Netlify Functions 及 server.js 等程式碼檔案，完整遷移回主 Repo 的官方子目錄：`C:\GOOGLE ANGET\第一類_核心網頁與互動系統\互動式網站`，並已刪除原本獨立的 `interactive-web-training` 目錄，確保 git 狀態由總庫唯一管理。

### 📌 Level 5 雙端即時互動簡報系統 (新增功能)
* **最新模組自動回退 (Gemini Fallback Chain)**：在後端 `server.js` 中實作了智能回退機制，當最新發布的 `gemini-3.6-flash` 出現 503 服務未就緒時，系統會自動無縫向下次級模組（`gemini-3.5-flash`、`gemini-2.5-flash` 等）嘗試，直至成功。
* **網頁端自訂 Gemini Key 與頁數**：在 `lv5-tutor.html` 右上角新增了金鑰與生成頁數選單，支援講師在 UI 介面上手動指定 4-15 頁的精準生成規格。
* **簡報/測驗線上即時修改**：在講師端卡片上新增了「📝 編輯此頁」與「📝 編輯此題」按鈕，允許講師在生成後於網頁上即時修改 Typos、測驗選項、正確答案與解析，並在儲存時透過 `/api/update-slides` 秒級同步到所有學員端。
* **自動存檔與 CSV 匯出**：
  - 實作了本機實體檔案 `data/classroom_save.json` 存檔，任何作答與教材修改都會自動持久化，重啟伺服器可完美還原。
  - 新增「📥 匯出答題紀錄」與「🧹 清除歷史」按鈕，可一鍵匯出含 UTF-8 BOM（防亂碼）的 Excel CSV 作答成績單。

### 📌 給另一台電腦的接手指示：
1. 本地開發伺服器啟動方式：進入 `C:\GOOGLE ANGET\第一類_核心網頁與互動系統\互動式網站\` 執行 `node server.js`（埠號 8888）。
2. 可直接修改或使用 UI 金鑰與選單，體驗全新的一鍵 AI 生成簡報、多人同步作答及即時成績匯出。

---

## 📅 最新交接紀錄 (2026-08-03)

### 🚨 發生錯誤：雙庫架構混淆導致原始碼遺失
* **狀況描述**：在公司操作時，不小心將只包含說明書的網頁版專案大廳 (`agent-portal` 的結構) 推送並覆蓋到了存放完整程式碼的 `google-agent` 總庫。導致三大類別底下的子資料夾 (程式碼、指令碼等) 全部消失，只剩下 `.md` 說明檔。
* **發生原因**：公司與家中電腦對於「更新大廳」與「更新總庫」的操作方式混淆。未明確區分 `agent-portal` (僅用於 Cloudflare Pages 顯示的輕量說明書庫) 與 `google-agent` (完整原始碼與子資料夾)。

### 💡 解決方式與防呆指南 (避坑必讀！)
1. **雙庫各自獨立，絕不可互相強制覆蓋**：
   * **`google-agent` (本機路徑 `C:\GOOGLE ANGET`)**：這是「唯一」擁有所有子資料夾、原始碼的真實專案庫。**任何程式碼的修改、新增，都只能 push 到這裡。**
   * **`agent-portal`**：這只是一個「被動接收結果」的靜態網頁庫，裡面**正常情況下就應該只有 `.md` 說明書與 `index.html`**。
2. **大廳更新標準流程**：
   * 往後若要更新專案大廳，**一律使用 `python portal_tools\push_portal.py`** 腳本。
   * 此腳本會自動將最新的說明書打包，並**單獨**推送到 `agent-portal`，不會干擾 `google-agent`。
3. **強制目錄規範 (所有子專案)**：
   * 根據 `AGENTS.md` 規範，所有子專案的 `README.md` **必須** 包含「完整檔案結構說明 (File Tree)」與各檔案簡述。
   * **AI 守則**：當 AI 在處理任何子專案時，若發現沒有 File Tree 或是沒有目錄簡述，必須立刻補齊。這樣即使發生檔案遺失，另一台電腦也能透過 README 知道原本該有哪些結構，不會一錯再錯。

### 📌 給另一台電腦 (公司) 的接手指示：
當您在公司電腦開工時：
1. **千萬不要**再把公司舊的、只有說明書的 `main` 分支推上來。
2. 請執行 `git pull`，確保把今天在家裡（筆電）救回來、包含所有「子資料夾」的正確 `google-agent` 程式碼全部抓下來。
3. 若遇衝突，請直接放棄公司電腦的變更，以 GitHub 上最新的這版為主 (可使用 `git reset --hard origin/main`)。

---

## 📅 最新交接紀錄 (2026-08-03 下午)

### 🚨 發生錯誤：料號條碼首字為 1 或 7 被誤判為批號格式錯誤
* **狀況描述**：測試人員反應只有在掃描料號時無法自動跳下一欄，其餘欄位正常。
* **發生原因**：
  1. 舊相機掃描監聽器 `barcodeLauncher` 會對所有欄位執行 `validate17Series` (驗證是否符合 1開頭20碼、7開頭29碼且含-T0 的批號格式)。
  2. 現場使用的料號字串剛好以 `1` (如 `1L140024`) 或 `7` (如 `7L1400241-T02`) 開頭，導致被驗證器誤判定為「格式不符的批號」，欄位被清空並跳出格式錯誤 Toast，阻斷了自動跳欄焦點。
* **解決方式 (v1.9 成果)**：
  1. 重構 `MainActivity.kt`：**掃描時免驗證，送出時一次比對**。
  2. 移除了相機掃碼 `barcodeLauncher` 中的 `validateBarcodeFormat`。現在任何掃描文字皆能直接寫入輸入框並順利跳欄。
  3. 將所有的格式驗證、匹配邏輯、重複掃描檢查全部延遲至點擊「🚀 巡檢核對並存檔」時的 `performLocalCheck` 統一進行核對。

### 📌 給另一台電腦 (公司) 的接手指示：
1. **已將最新版本打包編譯為 `N-系列出貨核對-v1.9.apk`**。
2. 請執行 `git pull` 以拉取變更，並在 `n-series-gas-apk-offline` 目錄下雙擊 **`一鍵推送至GitHub.bat`** 完成子庫 Push。
3. **備份狀態**：已於 2026-08-03 執行 Gradle clean 並完成 Google Drive 備份存檔 (路徑為 `G:\我的雲端硬碟\GOOGLE ANGET\專案備份\n-series-gas-apk-offline`)。


### 🐛 嚴重錯誤防呆日誌：Cloudflare SPA 相對路徑死迴圈 (2026-08-04)
**發生原因**：
1. 大廳的 index.html (SPA 網站) 在 Markdown 解析器中，將圖片 ![image](assets/1.png) 錯誤地解析成了文字超連結 <a href= (因為缺乏對 ! 的避開檢查)。
2. 當使用者點擊被誤判為超連結的圖片時，瀏覽器會將相對路徑疊加到網址後方（例如 https://google-agent.pages.dev/assets/1.png）。
3. Cloudflare Pages 找不到檔案，自動觸發 SPA 路由返回 index.html（專案大廳）。
4. 導致使用者畫面退回大廳，但**網址列卡在錯誤的深層路徑**！
5. 在此狀態下繼續點擊，會產生更深的無窮迴圈路徑，導致畫面崩潰空白。

**正確處理步驟（已於 2026-08-04 修復）**：
1. **修正 Markdown 解析器**：加入圖片專用正則表示式，並將 SPA 圖片強制補上絕對路徑 (結合 mdPath 找出父資料夾)。
2. **修正連結解析**：將一般超連結的解析改為 /(^|[^!])\[([^\]]+)\]\(([^)]+)\)/g，避免抓取到圖片。
3. **防護手動按鈕**：所有手寫的相對路徑 `<a>` 標籤，都加入 onclick 以絕對路徑取代。

---

### 🐛 嚴重錯誤防呆日誌：Cloudflare SPA 啟動連結相對路徑巢狀死迴圈（第二波，2026-08-07）

**發生時間**：2026-08-07 上午  
**影響範圍**：說明書大廳（https://google-agent.pages.dev）所有的「立即啟動」按鈕

#### 🔍 根本原因（必讀！往後絕不能再犯）

```
錯誤根源：在 Cloudflare Pages 上部署 SPA（單頁應用）時，
使用「相對路徑」作為跳轉連結，會與 Cloudflare 的 SPA fallback
機制產生致命衝突。
```

**完整連鎖反應流程：**

1. 大廳的每個系統卡片有「🚀 立即啟動」按鈕，原本 `launchUrl` 寫的是相對路徑，例如：  
   `"launchUrl": "projects/interview_analyzer/index.html"`

2. 使用者在大廳（`https://google-agent.pages.dev/`）點擊後，瀏覽器導向：  
   `https://google-agent.pages.dev/projects/interview_analyzer/index.html`

3. Cloudflare Pages 找不到這個實體檔案 → 自動觸發 SPA fallback → **回傳 index.html（大廳本身）**

4. 大廳載入後，偵測到目前網址是 `/projects/interview_analyzer/index.html`，**誤判自己被從子路徑載入**

5. 接著大廳的 JS 用 `window.location.href` 嘗試跳轉，**但因為已在子路徑，相對路徑又往深層疊加一層**

6. 變成：`https://google-agent.pages.dev/projects/interview_analyzer/projects/interview_analyzer/index.html`

7. **無窮巢狀迴圈**，URL 越來越長，最終頁面崩潰空白

#### ✅ 三層修復方案（已於 2026-08-07 全部實施）

| 層級 | 修改內容 | 位置 |
|---|---|---|
| **第 1 層** | 新增 `_redirects` 規則：`/* /index.html 200`，確保 Cloudflare 正確處理所有路由 | `說明書/_redirects` |
| **第 2 層** | 加入 SPA 啟動防護 Guard：偵測到 URL 包含非根路徑時，立即 `window.history.replaceState` 回根目錄再渲染 | `說明書/index.html` JS 頂部 |
| **第 3 層** | **最根本修復**：將所有系統卡片的 `launchUrl` 從相對路徑改為絕對 Cloudflare Pages URL，例如：`"launchUrl": "https://google-agent.pages.dev/projects/interview_analyzer/"` | `說明書/index.html` JSON 資料區 |

#### 🚨 往後 AI 開發大廳或 SPA 的鐵律（違反即導致死迴圈）

> **在 Cloudflare Pages 上的 SPA 大廳，所有跳轉連結（launchUrl、href、window.location）一律使用「絕對路徑」，禁止使用相對路徑。**

```javascript
// ❌ 錯誤寫法（會觸發巢狀死迴圈）
launchUrl: "projects/interview_analyzer/index.html"
window.location.href = "projects/..."

// ✅ 正確寫法（使用完整絕對 URL）
launchUrl: "https://google-agent.pages.dev/projects/interview_analyzer/"
window.location.href = "https://google-agent.pages.dev/projects/..."
```

#### 📌 新增連結時的 Checklist
- [ ] `launchUrl` 是否為完整 https:// 開頭的絕對路徑？
- [ ] `_redirects` 檔案是否存在且包含 `/* /index.html 200`？
- [ ] SPA Guard（防止子路徑誤載）是否在 index.html 頂部 JS 中？
 
 
### 📅 2026-08-16 交接紀錄 (台積三合一單與COA 雙重核對系統)
**今日完成進度：**
1. **設定與程式碼分離 (Configuration Decoupling)**：將原本寫死在 程式碼.gs 的金鑰與設定，全面移至 Google 試算表 設定 分頁，支援多組 Google Vision 與 Gemini 金鑰動態輪替。
2. **多模型+多金鑰瀑布流降級機制**：實作雙迴圈架構，當 Vision 失敗時自動接手 Gemini，從 3.6-flash 到 3.1-flash-lite，針對每個模型輪替所有可用金鑰，極大化白嫖免費額度。
3. **系統 API 日誌紀錄 (API_Log)**：實作自動化日誌紀錄，紀錄每次 API 呼叫的狀態、使用的模型與遮蔽後的金鑰。

**避坑指南 / 注意事項：**
* USAGE_LIMIT (預設 900) 必須填寫在試算表的 B 欄 (設定值)。
* 程式碼裡有保留了安全底線，如果試算表設定意外被刪除，不會當機。
