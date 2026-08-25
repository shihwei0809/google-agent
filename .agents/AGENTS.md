# 🤖 專案開發規範：AI 引導與一鍵安裝標準 (AI-Guided & One-Click Setup)

為了使本專案內的所有工具與網頁系統具備極高的可移植性與 AI 自動維護性，往後所有專案（包含主系統目錄與所有子專案資料夾）的建立與修改皆須嚴格遵循以下「標準三件套」設計：

## 1. 專案必要檔案結構 (主系統與所有子專案皆須具備)
每個獨立專案或子資料夾必須包含以下三個核心檔案：
1. **`README.md`**：【給人類閱讀】高質感 Markdown 說明書，使 GitHub 自動渲染。必須包含：
   - 專案名稱與簡介 (必須清楚寫明專案目的)
   - 核心功能亮點 (Bullet points)
   - 完整檔案結構說明 (File Tree，**這是跨電腦同步防呆的關鍵，只要是專案都必須有目錄結構與各檔案簡述**)
   - 跨電腦一鍵啟動與執行步驟
2. **`SKILL.md`**：【給 AI 助理閱讀】說明書。定義該專案的名稱、依賴環境、執行指令，以及如何引導使用者進行環境設定與安裝。
3. **`setup_env.ps1`**：【給真人或 AI 助理執行】的一鍵安裝/環境設定 PowerShell 腳本。必須自動偵測系統環境、安裝必要的套件（如 pip 套件、npm 套件、Netlify CLI 等）。

## 2. AI 助理行為規範
* **引導優先**：當 AI 助理開啟新專案或被調用至特定子專案時，必須優先檢查該目錄下的 `SKILL.md`。若環境尚未初始化，應主動詢問使用者是否要執行 `setup_env.ps1`。
* **說明書同步更新**：在新增任何功能、外部套件或改變執行方式時，必須同步更新 `README.md`、`SKILL.md` 與 `setup_env.ps1`，確保說明書與安裝指令永久可用。

## 3. 專案大廳、雙庫與部署平台全域速查

### GitHub 雙庫（絕不可互相覆蓋）
| 庫 | 帳號 | 用途 |
|---|---|---|
| `google-agent` | `shihwei0809` | **主庫**，所有程式碼、子專案原始碼唯一存放處 |
| `agent-portal` | `mathruffian-dot` | **展示庫**，只放大廳靜態 HTML，由 Cloudflare Pages 自動部署 |

### 四大部署平台
| 平台 | 網址 | 用於哪些專案 |
|---|---|---|
| ☁️ **Cloudflare Pages**（主要大廳） | https://google-agent.pages.dev | 說明書大廳（正式版） |
| 🟠 **Netlify**（備用/草稿） | https://cerulean-praline-6b314d.netlify.app | 說明書大廳（Draft 預覽） |
| 🔴 **Firebase Hosting** | 各子專案獨立站 | `aigc-music-video-hub`、`flowchart-web`、互動投票、簡報系統等 |
| ⚫ **GitHub Pages** | `mathruffian-dot.github.io/...` | 靜態工具、簡報類 |

### 其他連結
- 🧠 **中央大腦 (my-ai-brain)**：https://github.com/shihwei0809/my-ai-brain.git
- 🛠️ **跨電腦技能庫 (cross-device-agent-skills)**：https://github.com/mathruffian-dot/cross-device-agent-skills.git
- 💻 **本機大廳實體路徑**：`C:\\GOOGLE ANGET\\說明書\\index.html`
- ⚡ **本機一鍵開啟**：雙擊 `C:\\GOOGLE ANGET\\點我開啟Cloudflare線上大廳.bat`

### ⚠️ 雙庫防呆鐵律
- **程式碼修改** → 只 push 到 `shihwei0809/google-agent`（用 `origin`）
- **大廳更新** → 只能用 `一鍵更新大廳.bat`，絕不手動 push 到 `agent-portal`
- **Firebase 子專案** → 各自在子資料夾內用 `firebase deploy`，不影響主庫

## 3.5 部署平台選擇判斷規則（建立新專案時必須判斷）

建立任何新系統前，AI 必須先判斷系統類型，選擇正確部署平台：

| 系統類型 | 正確平台 | 錯誤示範 |
|---|---|---|
| 純靜態網頁（只顯示內容） | ☁️ Cloudflare Pages | — |
| **需要線上編輯 / 多人同步 / 即時資料** | 🔴 Firebase Hosting + **Firestore** | ❌ 不能只用 Cloudflare（資料功能會失效） |
| 有 Python 後端（FastAPI/Flask） | 本機 .bat 啟動，無法靜態部署 | ❌ 不能上傳到任何靜態平台 |

### 補充說明
- **多平台同時部署不會衝突**：Firestore 資料在雲端，跟網頁放在哪個平台無關，可以同時部署到 Firebase + Cloudflare 作為備用
- **判斷關鍵字**：當需求出現「多人共用」、「線上修改」、「即時同步」、「不需重新整理就更新」→ 必須引入 Firebase Firestore

## 4. 收工規則與雙機 Git 分支同步規範 (使用者說「收工」時必須執行)
每次使用者說「收工」，AI 必須按以下順序完成，並**嚴格遵守跨機 Git 分支邏輯**：
1. **主動詢問開發狀態 (Git 分支防呆判斷)**：
   - AI 必須先詢問：「*今天的進度都已經在測試環境驗證成功、準備正式上線了嗎？還是只是要備份跨機開發的進度？*」
   - **狀況 A（未完工/純備份）**：若使用者表示還沒寫完或只是備份，AI 必須建立或保留在 `feat/[當天日期]`（例如 `feat/20260825`）等開發分支，將修改 Commit 並 Push 到該分支。**絕對禁止**直接推送到 `main`。
   - **狀況 B（驗收完畢/正式上線）**：若使用者表示功能已完成且測試無誤，AI 必須將目前的開發進度合併至 `main`，並**自動執行「發布版本」流程（自動偵測現有 Tag 往上加 1、建立新 Tag，並連同 `main` 一起 Push 上雲端）**，確保 `main` 永遠是乾淨可用的正式版且具備最新版號。
2. **更新交接日誌**：將今日遇到的錯誤、解決步驟寫入專案根目錄的 `HANDOVER.md` (跨電腦交接日誌)。
3. **顯示今日完成項目表格**：格式為 `# | 功能 | 狀態`
4. **本機雙重備份 (Google Drive)**：自動將當天有修改的「子專案資料夾」打包或複製，存入 `G:\我的雲端硬碟\GOOGLE ANGET\專案備份`，**並且必須將備份腳本的執行結果 (Log) 以 Markdown `text` 區塊完整顯示給使用者看**。
5. **顯示 GitHub 推送結果**：包含推送的**分支名稱**、Commit hash (短版) 與 GitHub repo 連結。

## 5. 主動開工偵測規則 (防呆提醒)
當 AI 接收到使用者的第一句話，且判定為全新的對話或一天的開始，AI 必須主動在回覆的第一段詢問：
「*早安！偵測到新任務，需要我先幫您執行『開工』檢查（例如 git pull 取回雲端最新進度，並讀取 HANDOVER.md 了解上一次的開發狀態）嗎？*」
使用者同意（或主動說「開工」）後，必須按以下順序執行：
1. 執行 `git pull` 確保本機是最新的。
2. 讀取 `HANDOVER.md`，並**將 `HANDOVER.md` 內的「前次進度與交接事項」以 Markdown `text` 區塊完整顯示給使用者看**，確保雙方對齊開發狀態，避免踩到跨機的歷史錯誤陷阱。

## 6. 本機 Server 啟動與 Port 佔用自動處理規範
凡是在本機執行的 Web / API 伺服器專案，其啟動腳本或主程式必須遵循以下規範：
1. **顯示本機 IP 與網址**：啟動時除了顯示 `http://localhost:[PORT]` 外，**必須自動抓取並顯示本機實體 IP 位址**（例如 `http://192.168.x.x:[PORT]`），方便提供給區域網路同伴使用。
2. **Port 佔用自動切換 (Port Fallback)**：當預設 Port（如 8002）已被其他程式佔用時，系統**不得崩潰中斷**，必須自動搜尋並切換至下一個可用的 Port（如 8003, 8004...），並在主控台上明確提示「*預設 Port [原Port] 已被佔用，已自動切換至可用 Port: [新Port]*」。

## 7. 跨電腦交接與錯誤防呆日誌 (Cross-Device Handover)
為避免在公司與家中多台電腦切換時發生覆蓋錯誤，AI 必須維護根目錄的 **`HANDOVER.md`**：
1. **強制記錄**：在本機有任何結構改變、發生嚴重錯誤（例如推錯專案、無限迴圈）時，必須記錄其「發生原因」與「正確處理步驟」。
2. **跨機防呆**：當在另一台電腦讀取到此日誌時，AI 應嚴格遵循其上的「避坑指南」，確保不會用錯誤的方式上傳或執行指令。

## 8. 專案啟動 BAT 自動產生規範 (Auto-Generated Launcher)

**每當 AI 建立或修改任何具有 Python 後端的專案時，必須自動產生或更新該專案的 `.bat` 啟動檔。**

### AI 必須自動執行的動作：
1. **掃描專案的 `requirements.txt` 或 `main.py` 的 import 清單**，自動偵測所有需要的 pip 套件
2. **依據掃描結果，自動填入套件清單**，套用位於 `C:\GOOGLE ANGET\bat_launcher_template.bat` 的通用模板
3. **自動產生完整的 `.bat` 啟動檔**，不需使用者手動修改任何內容

### 產生的 BAT 必須包含以下功能（缺一不可）：
- ✅ 偵測 Python 是否安裝 → 未安裝則顯示提示並自動開啟下載頁
- ✅ 確認 pip 可用 → 損壞則自動修復
- ✅ 逐一 `import` 測試每個套件 → 缺少則自動 `pip install`（只裝缺少的，不重裝已有的）
- ✅ 建立專案必要資料夾（如 `data/`, `data/audios/`, `static/`）
- ✅ 自動偵測可用 Port（預設 Port 被佔用則自動切換）
- ✅ 顯示本機 IP 供同事區網連線使用
- ✅ 延遲 2 秒後自動開啟瀏覽器

### 套件掃描對照表（AI 必須知道的 import 名稱對照）：
| pip 安裝名稱 | Python import 名稱 |
|---|---|
| fastapi | fastapi |
| uvicorn | uvicorn |
| google-genai | google.genai |
| pydantic | pydantic |
| python-multipart | multipart |
| openpyxl | openpyxl |
| python-docx | docx |
| requests | requests |
| beautifulsoup4 | bs4 |
| flask | flask |
| numpy | numpy |
| pandas | pandas |
| pillow | PIL |
| python-dotenv | dotenv |
| aiofiles | aiofiles |

### 範例：AI 看到 requirements.txt 包含 fastapi, openpyxl, google-genai 時，必須自動產生：
```bat
set PKG[0]=fastapi|fastapi>=0.100.0
set PKG[1]=uvicorn|uvicorn>=0.22.0
set PKG[2]=google.genai|google-genai
set PKG[3]=openpyxl|openpyxl
set PKG_COUNT=4
```
**不得要求使用者自行修改 bat 檔內容。**