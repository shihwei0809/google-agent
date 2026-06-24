# AI Agent Obsidian 知識庫建置 (ai-anget) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/ai anget](https://github.com/shihwei0809/google-agent/tree/main/ai anget)


## 專案簡介
本專案定義並實作了一套供 AI Agent 自動執行的 **Obsidian 二次大腦知識庫自動建置與整理工作流**。系統能夠自動從指定的 YouTube 頻道中提取影片字幕、進行去重與清洗，並按照 Obsidian 三層架構（Clipping、創作庫、知識庫）進行整理，最後產出結構化的教學與簡報企劃。

## 主要功能特色
- **自動化字幕抓取與清洗**：利用 `yt-dlp` 下載頻道影片字幕，並自動過濾時間碼、HTML 標記，特別是針對 YouTube 自動字幕的「滾動重複行」進行去重處理。
- **三層 Obsidian 知識庫架構**：
  * **`Clipping/` (外部來源)**：存放最原始的影片逐字稿 Markdown 檔案。
  * **`創作庫/` (創作成果)**：存放本機的原創講義、腳本與教學草稿。
  * **`知識庫/` (核心知識)**：由 AI Agent 根據外部逐字稿整理出的結構化筆記與索引目錄。
- **Agent 定期自動整理**：設定 AI Agent 定期（如每週）掃描外部逐字稿與創作庫，提取關鍵詞、主題，自動生成知識庫筆記，並維護全域索引。

## 技術棧
- **開發語言**：Python 3
- **核心庫**：`yt-dlp` (YouTube 影片與字幕下載)
- **資料庫/視覺化**：Obsidian (Markdown 筆記關聯圖)

## 專案結構
- `extract_videos.py`：從指定頻道獲取影片中繼資料，並篩選關鍵詞影片網址。
- `download_all_subs.py`：循環下載並清洗字幕，導出為 Markdown 格式。
- `sync_projects.py`：專案與知識庫同步腳本。
- `sensebar_ai_urls.txt`：篩選出的影片網址清單。
- `sensebar_ai_videos.md`：影片與字幕提取紀錄。

## 本機執行與操作
1. **環境準備**：
   確保本機安裝了 Python，並安裝 dependencies：
   ```bash
   pip install yt-dlp
   ```
2. **提取影片網址**：
   執行以下腳本，獲取頻道內包含關鍵詞的影片清單：
   ```bash
   python extract_videos.py
   ```
3. **下載並清洗逐字稿**：
   執行以下腳本，將自動下載字幕並將其清洗為乾淨的 Markdown 逐字稿：
   ```bash
   python download_all_subs.py
   ```
4. **建立 Obsidian 資料夾**：
   在工作區建立 `Clipping`、`創作庫`、`知識庫` 三個資料夾，將產出的逐字稿放入 `Clipping/` 下。
5. **AI 代理整理**：
   指示 AI 代理（如 Antigravity）：「請讀取 `Clipping` 與 `創作庫` 資料夾，並在 `知識庫` 中建立結構化筆記與全域索引（`Index.md`）」。
