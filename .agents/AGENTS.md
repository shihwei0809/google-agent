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

## 6. 本機 Server 啟動與 Port 佔用自動處理規範
凡是在本機執行的 Web / API 伺服器專案，其啟動腳本或主程式必須遵循以下規範：
1. **顯示本機 IP 與網址**：啟動時除了顯示 `http://localhost:[PORT]` 外，**必須自動抓取並顯示本機實體 IP 位址**（例如 `http://192.168.x.x:[PORT]`），方便提供給區域網路同伴使用。
2. **Port 佔用自動切換 (Port Fallback)**：當預設 Port（如 8002）已被其他程式佔用時，系統**不得崩潰中斷**，必須自動搜尋並切換至下一個可用的 Port（如 8003, 8004...），並在主控台上明確提示「*預設 Port [原Port] 已被佔用，已自動切換至可用 Port: [新Port]*」。

**Python 標準動態 Port 與 IP 綁定寫法範例**：
```python
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port
```