# 🔄 跨電腦交接與防呆日誌 (HANDOVER)

**目的**：記錄跨電腦開發的狀態、發生過的嚴重錯誤與避坑指南。AI 助理在「開工」時必須優先閱讀此檔案，以避免踩雷或引發無限錯誤迴圈。

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
