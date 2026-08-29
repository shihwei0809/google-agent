# Google Agent 工作流與專案管理大腦

本倉庫為個人 AI Agent 工作流與專案管理的核心大腦，包含自動同步工具、Obsidian 知識庫與專案駕駛艙。

## 專案結構

- `ai anget/`: 包含 AI 工作流的核心腳本與第二大腦知識庫。
  - `sync_projects.py`: 自動同步多個專案的 Python 腳本。
  - `build_my_vault.py`: 用於建立或編譯 Obsidian 知識庫的腳本。
  - `知識庫/`: 包含個人 Obsidian 專案駕駛艙與索引。
  - `Clipping/`: 保存從網路或 YouTube 下載完的逐字稿與筆記。
- `一鍵同步專案.bat`: 用於一鍵執行同步專案的 Windows 批次檔。
- `專案總覽.html`: 網頁版的專案駕駛艙，便於快速預覽與導覽所有專案。
- `ANTIGRAVITY.md`: AntiGravity 代理的本地工作規範與路徑設定。

## 使用方式

雙擊執行 `一鍵同步專案.bat`，將自動觸發 `ai anget/sync_projects.py` 來進行各專案的自動化同步與備份。
