# 🔄 跨電腦交接與防呆日誌 (HANDOVER)

**目的**：記錄跨電腦開發的狀態、發生過的嚴重錯誤與避坑指南。AI 助理在「開工」時必須優先閱讀此檔案，以避免踩雷或引發無限錯誤迴圈。

---

## 📅 最新交接紀錄 (2026-08-14) ⭐ 最新

### 📌 ISOTANK 條碼產生器與 Excel 自動化升級 (`isotank bacode.xlsx`)
* **3cm 條碼自動置中 (OpenXML EMU Anchor)**：計算 24 欄寬與 115 pt 列高的邊距偏移量 (`colOff=36px`, `rowOff=20px`)，將所有 3.0 cm (114px) QR Code 條碼實現水平與垂直雙向完美置中。
* **分類歸位校正**：將原本誤歸入 `E33X` 的 `E329` 槽號正確歸位至 `E32X (10個)` 分頁。
* **資料去重與全分頁重新生成**：依據去重後的 156 個真實槽號，自動分類並重新生成全檔 16 個標籤分頁 (全檔共 17 個分頁)，剔除非槽號數字雜訊與測試碼 `E400~E402`。
* **批次一鍵/拖曳匯入工具 (`add_isotank_code.py` / `雙擊點我快速新增槽車條碼.bat`)**：
  - 升級為「按下 Enter 即時秒級執行」，免按 Ctrl+Z。
  - 支援拖曳 `.xlsx` / `.txt` / `.csv` 檔案或整欄貼上槽號，全格自動掃描比對槽號特徵。
  - **雙向同步寫入**：新增槽號時自動同步寫入第 1 分頁 (`oracle_sync_data`) 的槽號/罐號/容量及對應分類標籤分頁。
  - **控制台 CP950 防呆**：移除 `print()` 內的 emoji 符號，解決 Windows CP950 cmd.exe 終端拋出 `UnicodeEncodeError` 錯誤。

---

## 📅 最新交接紀錄 (2026-08-13)

### 📌 AI 面試語音分析系統 (`interview_analyzer`) 跨電腦啟動與編碼防呆重構
* **PowerShell UTF-8 BOM 編碼修復**：`setup_env.ps1` 原先無 BOM 格式導致 Windows PowerShell 5.1 繁體中文環境下將中文字元誤判為雙引號終結符 (`TerminatorExpectedAtEndOfString`)，已改寫為標準 UTF-8 with BOM (`utf-8-sig`) 編碼，確保 100% 成功執行。
* **跨電腦 .venv 硬編碼路徑自動清理**：修改 `雙擊點我啟動面試語音AI分析系統.bat`，啟動時自動檢測 `.venv` 是否能在本機正常運行。若為從其他電腦複製過來的無效環境，自動刪除舊 `.venv` 並調用 `setup_env.ps1` 重新建置。
* **未安裝 Python 時背景自動靜默安裝**：`setup_env.ps1` 新增 `winget` 與 Python 官方 64 位元靜默安裝器 (`/quiet PrependPath=1`) 雙重自動背景安裝邏輯，若同仁電腦未安裝 Python 可一鍵背景安裝並自動設定 PATH。
* **.gitignore 隔離**：新增 `.gitignore` 避免 `.venv` 誤推上雲端干擾其他電腦。

### 📌 給另一台電腦的接手指示：
1. 進入 `第三類_AI代理與指南企劃/interview_analyzer` 雙擊 `雙擊點我啟動面試語音AI分析系統.bat` 即可一鍵傻瓜式自動完成環境設定與開啟系統。

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

## 📅 最新交接紀錄 (2026-08-07) ⭐ 最新

### ✅ 今日完成：大廳連結 URL 疊加問題 — 根本修復

**問題根本原因**：
- 大廳 `說明書/index.html` 中所有子專案連結都使用 `./projects/xxx` 相對路徑
- Cloudflare Pages 的 SPA fallback 把所有找不到的路徑都回傳大廳的 `index.html`，但 URL 不更正
- 造成每次點擊後 URL 不斷疊加（如 `/projects/flowchart-web/projects/hr_quiz_v2/...`）

**解決方式：每個子專案各自部署為獨立的 Cloudflare Pages 專案**

### 🌐 子專案獨立 Cloudflare Pages 部署清單（2026-08-07 建立）

| 子專案 | 永久網址 | Wrangler 專案名稱 |
|-------|---------|-----------------|
| 儲槽氮氣閥教育訓練 | https://nitrogen-valve-training.pages.dev | `nitrogen-valve-training` |
| 員工教育訓練測驗 | https://hr-quiz-v2.pages.dev/index_with_mp3.html | `hr-quiz-v2` |
| 軟管對刷稽核 | https://hongsheng-web-portal.pages.dev | `hongsheng-web-portal` |
| isotank-training | https://isotank-training.pages.dev | `isotank-training` |
| isotank-hf-demo | https://isotank-hf-demo.pages.dev | `isotank-hf-demo` |
| 大阪冒險電子書 | https://osaka-book.pages.dev | `osaka-book` |
| 互動式網站 Lv1-5 | https://interactive-site.pages.dev | `interactive-site` |
| Padlet 留言板 | https://padlet-board-app.pages.dev | `padlet-board-app` |

### 💡 專案導覽策略更新 (2026-08-10)
- **子專案「返回大廳」按鈕處理決策**：經討論後決定**不再逐一修改**各子專案內部的「返回大廳」按鈕。因為大廳的「進入系統」已預設使用新分頁 (`target="_blank"`) 開啟，使用者只需關閉子專案分頁即可回到原先保留的大廳畫面，這在 UX 上是更好且維護成本更低的設計。

### 🔧 重新部署任何子專案的標準指令
```powershell
# 排除大檔案後部署
$src = "說明書\projects\<資料夾名稱>"
$tmp = "$env:TEMP\<資料夾名稱>_deploy"
Copy-Item $src $tmp -Recurse
Get-ChildItem $tmp -Recurse | Where-Object { $_.Length -gt 25MB } | Remove-Item -Force
wrangler pages deploy $tmp --project-name "<cloudflare-project-name>" --commit-dirty=true
```

### 🔧 重新部署主大廳的標準指令（排除大檔案）
```powershell
$tmp = "$env:TEMP\portal_deploy_clean"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Copy-Item "說明書" $tmp -Recurse
Get-ChildItem $tmp -Recurse | Where-Object { $_.Length -gt 25MB } | Remove-Item -Force
wrangler pages deploy $tmp --project-name "google-agent" --commit-dirty=true
```

### ⚠️ 重要：大廳更新後必須用 Wrangler 直接部署
- `git push` **不會自動觸發** Cloudflare Pages 更新（GitHub 與 Cloudflare 連結可能斷開）
- 每次修改 `說明書/index.html` 後，必須執行上面的「重新部署主大廳」指令
- `說明書/projects/hr_quiz_v2/MP3生成工具.exe` 是 35.2MB 的大檔案，**每次部署都必須排除**（已寫入腳本中）

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
