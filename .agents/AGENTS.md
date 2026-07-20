# 🤖 專案開發規範：AI 引導與一鍵安裝標準 (AI-Guided & One-Click Setup)

為了使本專案內的所有工具與網頁系統具備極高的可移植性與 AI 自動維護性，往後所有專案的建立與修改皆須遵循「AI 引導與一鍵安裝」的標準設計：

## 1. 專案必要檔案結構
每個獨立專案（或子資料夾）必須包含以下兩個核心檔案：
1. **`SKILL.md`**：給 AI 助理（如 Antigravity / Claude Code）閱讀的說明書。定義該專案的名稱、依賴環境、執行指令，以及如何引導使用者進行環境設定與安裝。
2. **`setup_env.ps1`**：給真人或 AI 助理執行的一鍵安裝/環境設定 PowerShell 腳本。必須自動偵測系統環境、安裝必要的套件（如 pip 套件、npm 套件、Netlify CLI 等）。

## 2. AI 助理行為規範
* **引導優先**：當 AI 助理開啟新專案或被調用至特定子專案時，必須優先檢查該目錄下的 `SKILL.md`。若環境尚未初始化，應主動詢問使用者是否要執行 `setup_env.ps1`。
* **自動維護**：在新增任何外部套件或改變執行方式時，必須同步更新 `SKILL.md` 與 `setup_env.ps1`，確保安裝指令永久可用。

## 3. 專案大廳與雙庫線上入口記憶 (全域速查)
- ☁️ **Cloudflare Pages 線上正版大廳**：https://google-agent.pages.dev
- ☁️ **Cloudflare Pages 備用大廳**：https://agent-portal.pages.dev
- 🧠 **中央大腦 (my-ai-brain)**：https://github.com/shihwei0809/my-ai-brain.git
- 🛠️ **跨電腦技能庫 (cross-device-agent-skills)**：https://github.com/mathruffian-dot/cross-device-agent-skills.git
- 💻 **本機大廳實體路徑**：`D:\GOOGLE ANGET\說明書\index.html`
- ⚡ **本機一鍵開啟**：雙擊 `D:\GOOGLE ANGET\點我開啟Cloudflare線上大廳.bat`

## 4. 收工規則與雙重備份 (使用者說「收工」時必須執行)
每次使用者說「收工」，必須按以下順序完成：
1. **顯示今日完成項目表格**：格式為 `# | 功能 | 狀態`
2. **自動將當天有修改的「子專案資料夾」打包或複製**，存入 `G:\我的雲端硬碟\GOOGLE ANGET\專案備份` (完成 Google Drive 本機實體備份)
3. **自動執行 git add + commit + push**：將本次所有修改推上 GitHub。
4. **顯示 GitHub 推送結果**：包含 Commit hash (短版) 與 GitHub repo 連結。

## 5. 主動開工偵測規則 (防呆提醒)
當 AI 接收到使用者的第一句話，且判定為全新的對話或一天的開始，AI 必須主動在回覆的第一段詢問：
「*早安！偵測到新任務，需要我先幫您執行『開工』檢查（例如 git pull 取回雲端最新進度）嗎？*」
使用者同意後，再執行 git pull。

## 6. 本機 Server 啟動批次檔 (.bat) 顯示 IP 規範
凡是在本機執行的 Web / API 伺服器專案，其一鍵啟動批次檔 (`.bat`) 中除了顯示 `localhost` 與 Port 號之外，**必須自動抓取並顯示本機實體 IP 位址**（方便使用者將網址提供給同區域網路/同網域旁人使用，無需手動查詢 IP）。

**標準 BAT 提示範例與指令**：
```bat
for /f "tokens=*" %%a in ('powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object IPAddress -notlike '127.*' | Where-Object IPAddress -notlike '169.254.*' | Select-Object -ExpandProperty IPAddress)[0]"') do set LOCAL_IP=%%a

echo ===================================================
echo    [專案名稱] (Port [PORT])
echo.
echo    本機開啟網址:
echo    http://localhost:[PORT]
echo.
echo    同網域 / 旁人使用網址:
echo    http://%LOCAL_IP%:[PORT]
echo ===================================================
```
