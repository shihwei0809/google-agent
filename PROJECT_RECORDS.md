# GOOGLE ANGET 專案總覽與備份紀錄 (Project Records)

此文件記錄了 `G:\我的雲端硬碟\GOOGLE ANGET` 目錄下所有主要專案的內容與用途，方便後續人員接手、更新與維護。

## 核心專案清單

### 1. 軟管對刷稽核系統 (hongsheng-web)
- **GitHub 專案連結**：[google-agent/hongsheng-web](https://github.com/shihwei0809/google-agent/tree/main/hongsheng-web)
- **用途**：鴻勝化學的「軟管對刷稽核系統 — 互動式教育訓練與模擬演練」網頁應用程式。
- **技術棧**：HTML, CSS, JavaScript, Firebase Firestore。
- **功能特色**：包含暗黑科技風格 UI、Firebase 即時資料庫連線狀態指示、多模式切換（簡報模式、模擬演練模式）、終端機風格的現場操作員模擬、以及掃描器視覺特效與 QC 檢驗儀表板。

### 2. 產品製程流程圖系統 (flowchart-web)
- **GitHub 專案連結**：[google-agent/flowchart-web](https://github.com/shihwei0809/google-agent/tree/main/flowchart-web)
- **用途**：鴻勝化學的「產品製程流程圖系統 (槽體製程管控系統)」。
- **技術棧**：HTML, CSS, JavaScript。
- **功能特色**：提供側邊欄導航、圖例說明（原料、製程、成品槽、格外品）、 SVG 互動式流程圖畫布。支援匯入/匯出備份功能，以及點擊槽體跳出詳細資訊（包含液位動態視覺、溫度、壓力、成分狀態），並支援 N2 吹掃模擬。

### 3. ISOTANK 化學品卸料安全訓練 (isotank-training)
- **GitHub 專案連結**：[google-agent/isotank-training](https://github.com/shihwei0809/google-agent/tree/main/isotank-training)
- **用途**：ISOTANK 化學品進貨安全與卸料訓練的互動式簡報/動畫網頁。
- **技術棧**：HTML, CSS, 內嵌 SVG 動畫。
- **功能特色**：高度視覺化的安全教育訓練教材，包含 9 個步驟（如隱形危機、進場核對、雙重防線、接管氣密等），結合 SVG 動畫演示防溢流堤架設、接地測試、管線對接氣密測試等，並配有旁白字幕與時間軸控制腳本。

### 4. Claude HTML 簡報生成技能 (claude-html-slide-builder)
- **GitHub 專案連結**：[claude-html-slide-builder](https://github.com/mathruffian-dot/claude-html-slide-builder)
- **用途**：供 Claude Code 使用的 Skill 工具，能將文字教材自動轉換成 Reveal.js 的 HTML 互動簡報。
- **技術棧**：Python, Reveal.js, wordcloud2.js, Firebase, GitHub CLI。
- **功能特色**：支援 AI 生成背景底圖、自動圖標去背、即時 Firebase 文字雲與投票互動元件、以及自動部署至 GitHub Pages 的功能。

### 5. Clasp + Netlify 部署指南 (clasp-netlify-mcp-guide)
- **GitHub 專案連結**：[clasp-netlify-mcp-guide](https://github.com/mathruffian-dot/clasp-netlify-mcp-guide)
- **用途**：標準安裝與避坑部署指南，指導 AI Agent（如 Antigravity, Claude Code 等）如何自動化建置「網頁前端 + Google Sheets 資料庫 (GAS) + Netlify」的閉環系統。
- **技術棧**：Node.js, Google Apps Script (clasp), Netlify。
- **功能特色**：包含五大經典踩坑注意事項，以及完整的環境配置腳本說明。

### 6. LINE 飲食熱量精算師 (根目錄產生腳本)
- **GitHub 專案連結**：[google-agent](https://github.com/shihwei0809/google-agent)
- **用途**：透過 `generate_docs.py` 自動生成「LINE 飲食熱量精算師：Gemini 2.5 + GAS 完全建置手冊」的 PDF 與 PPTX 檔案。
- **相關檔案**：`generate_docs.py`, `LINE_Diet_Bot_Tutorial.pdf`, `LINE_Diet_Bot_Tutorial.pptx`, `README.md`, `requirements.txt`。

### 7. 其他簡報自動化與旅遊企劃
- **GitHub 專案連結**：[google-agent](https://github.com/shihwei0809/google-agent)
- **自動化 PPT 腳本**：根目錄包含多個 Python 腳本（如 `generate_hongsheng_ppt.py`, `generate_optimized_flowchart_ppt.py`），用於自動產生特定業務流程或優化版的 PowerPoint 簡報。
- **旅遊企劃**：如 `grad-trip` (畢業旅行)、`大阪五天四夜自由行.pptx`、`沖繩自由行規劃_2大2小.md` 等生活與旅遊規劃檔案。

### 8. 大阪冒險之旅四格漫畫電子書 (test)
- **GitHub 專案連結**：[google-agent/test](https://github.com/shihwei0809/google-agent/tree/main/test)
- **用途**：小妤一家四口大阪五天四夜旅遊的四格漫畫互動式電子書，整合雙語音播放（微軟原生台灣國語與ElevenLabs電影級語音）與角色試聽功能。
- **技術棧**：HTML, CSS, JavaScript, Python (edge-tts), ElevenLabs API。
- **功能特色**：
  - **微軟原生 (Microsoft Native) 模式**：已優化各角色原生台灣腔聲線；特別針對 10 歲主角弟弟「小融 (Taiga)」的語音進行校正，採用微軟台灣男聲 `zh-TW-YunJheNeural` 作為基底，結合 `+35Hz` 音高及 `+15%` 語速調整，完美模擬出活潑的 10 歲小男孩童音，拒絕女聲混淆。
  - **ElevenLabs 模式**：支援付費帳號的高擬真自訂配音，且設有免費額度耗盡時自動降級的防錯機制。
  - **試聽面板**：在設定彈窗中提供個別角色語音試聽功能（試聽小妤、小融、爸爸、媽媽），方便讀者預覽音色。

### 9. 溫度通報系統本機與雲端同步備援機制 (溫度通報)
- **GitHub 專案連結**：[google-agent/溫度通報](https://github.com/shihwei0809/google-agent/tree/main/溫度通報)
- **用途**：溫度高溫通報系統的 v2.2 版本更新，實現本機 (Windows 排程) 與雲端 (Google Apps Script) 雙向狀態同步與主/備援運作。
- **功能特色**：
  - **本機優先，雲端備援**：本機每小時檢查完後會向雲端發送心跳。若本機斷線或關機（超過 75 分鐘無心跳），雲端將自動接手溫度監控與發送通知（在通知狀態內標註為「雲端備援」）。
  - **雙向狀態同步**：本機啟動時自動透過 API 與雲端同步最新警報狀態（`LAST_STATE`），避免本機重開機後發生重複通報。
  - **免開程式碼測試與重置**：雲端 GAS 新增 `onOpen()` 自動選單與獨立的測試函式，可直接在試算表中一鍵測試通報，或重置重複通知鎖定狀態。
- **主要變更檔案**：
  - `weather_monitor.py`：本機 Python 監控腳本，新增心跳回報與開機同步。
  - `config.json`：新增 `"web_app_url"` 配置項。
  - `複製雲端代碼.py` 及 `雲端GoogleAppsScript說明.md`：更新 Apps Script 腳本以支援心跳 API。

### 10. AI 克隆聲音 (AI 克隆聲音)
- **GitHub 專案連結**：[voxcpm2-voice-cloner](https://github.com/shihwei0809/voxcpm2-voice-cloner)
- **用途**：用 VoxCPM2 克隆使用者或指定角色的音色與語調，支援網頁錄音與 AI Agent 自然語言指令連動。
- **技術棧**：Python 3.12, Gradio (WebUI), VoxCPM2, PyTorch。

### 11. ISOTANK 化學品卸料安全訓練動畫與影片 (isotank-hf-demo)
- **GitHub 專案連結**：[google-agent/isotank-hf-demo](https://github.com/shihwei0809/google-agent/tree/main/isotank-hf-demo)
- **用途**：使用 HyperFrames 影音框架生成的化工廠安全卸料 12 頁動畫簡報與高畫質 MP4 影片。
- **技術棧**：HTML5, CSS3, GSAP, HyperFrames CLI, edge-tts, FFmpeg。

### 12. AI Agent Obsidian 知識庫建置 (ai anget)
- **GitHub 專案連結**：[google-agent/ai anget](https://github.com/shihwei0809/google-agent/tree/main/ai%20anget)
- **用途**：自動化 YouTube 頻道影片字幕提取、清洗與 Obsidian 三層式（Clipping、創作庫、知識庫）二次大腦知識庫整理。
- **技術棧**：Python, yt-dlp, Obsidian Markdown。

### 13. AIGC 音樂影片生成系統 (aigc-music-video-hub)
- **GitHub 專案連結**：[google-agent/aigc-music-video-hub](https://github.com/shihwei0809/google-agent/tree/main/aigc-music-video-hub)
- **用途**：企業宣傳歌曲 AI 生成（Suno）、故事板自動分配與影音批次合成渲染儀表板，已託管於 Firebase。
- **技術棧**：FFmpeg, Python, Suno AI, Firebase Hosting。

### 14. Claude Video Specs 影片規格與技能指南 (claude-video-specs)
- **GitHub 專案連結**：[claude-video-specs](https://github.com/mathruffian-dot/claude-video-specs)
- **用途**：三類 Reveal-Slide 影音製作規格、自動安裝腳本以及打包為 Agent Skill 的開發工具包。
- **技術棧**：Reveal.js, Bash, Python, Agent Skills Packager。

### 15. 跨電腦一鍵備份與還原轉移系統 (C:\GOOGLE ANGET\ 根目錄)
- **GitHub 專案連結**：[google-agent](https://github.com/shihwei0809/google-agent)
- **用途**：供 AI Agent 與開發者使用的一鍵備份、還原與跨電腦環境部署系統，支援自動排程備份。
- **技術棧**：Windows PowerShell, Windows Task Scheduler, Batch 批次檔。
- **功能特色**：
  - **自動排程備份**：雙擊 `一鍵設定排程.bat` 可在 Windows 自動註冊排程任務，每月固定備份。
  - **一鍵技能備份**：備份全域 MCP 設定、自訂技能 (Prompt Skills) 與本機工作區技能至 Google Drive。
  - **一鍵轉移還原**：在新電腦上執行 `setup_new_computer.ps1` 可自動完成 Git、Node、Python 等環境安裝並還原所有技能。

---

### 16. 員工教育訓練測驗系統 (hr_quiz_v2)
- **GitHub 專案連結**：[google-agent/影片生成/hr_quiz_v2](https://github.com/shihwei0809/google-agent/tree/main/影片生成/hr_quiz_v2)
- **用途**：員工工作規則教育訓練及自動化測驗。
- **技術棧**：HTML, CSS, JavaScript, Google Apps Script (GAS)。
- **功能特色**：簡報展示與測驗作答合一，內建繁體中文語音朗讀、可調速播放，測驗完成後自動將結果寫入 Google 試算表（透過 Apps Script 雲端 API）。支援本機免安裝 Python 內網啟動伺服器分享，以及 GitHub Pages 雲端部署。

## 🔗 GitHub 專案同步連結對照表

本機所有專案的 GitHub 託管倉庫與目錄結構對應如下：

| 本機目錄 / 專案名稱 | GitHub 倉庫 / 遠端目錄連結 |
| :--- | :--- |
| **`C:\GOOGLE ANGET` (主專案庫)** | [shihwei0809/google-agent](https://github.com/shihwei0809/google-agent) |
| ├─ `flowchart-web` | [google-agent/flowchart-web](https://github.com/shihwei0809/google-agent/tree/main/flowchart-web) |
| ├─ `hongsheng-web` | [google-agent/hongsheng-web](https://github.com/shihwei0809/google-agent/tree/main/hongsheng-web) |
| ├─ `isotank-training` | [google-agent/isotank-training](https://github.com/shihwei0809/google-agent/tree/main/isotank-training) |
| ├─ `isotank-hf-demo` | [google-agent/isotank-hf-demo](https://github.com/shihwei0809/google-agent/tree/main/isotank-hf-demo) |
| ├─ `test` (大阪冒險電子書) | [google-agent/test](https://github.com/shihwei0809/google-agent/tree/main/test) |
| ├─ `聲音轉文字` (NoType) | [google-agent/聲音轉文字](https://github.com/shihwei0809/google-agent/tree/main/聲音轉文字) |
| ├─ `互動式網站` | [google-agent/互動式網站](https://github.com/shihwei0809/google-agent/tree/main/互動式網站) |
| ├─ `IPAHQ槽車掃描系統代碼原始APP優化` | [google-agent/IPAHQ槽車掃描系統代碼原始APP優化](https://github.com/shihwei0809/google-agent/tree/main/IPAHQ槽車掃描系統代碼原始APP優化) |
| ├─ `IPA-生產排程雙儲槽優化` | [google-agent/IPA-生產排程雙儲槽優化](https://github.com/shihwei0809/google-agent/tree/main/IPA-生產排程雙儲槽優化) |
| ├─ `n系列GAS-轉-APK-離線核對上傳` | [google-agent/n系列GAS-轉-APK-離線核對上傳](https://github.com/shihwei0809/google-agent/tree/main/n系列GAS-轉-APK-離線核對上傳) |
| ├─ `N系列BARCODE出貨核對` | [google-agent/N系列BARCODE出貨核對](https://github.com/shihwei0809/google-agent/tree/main/N系列BARCODE出貨核對) |
| ├─ `QC-系統客製化電子化工廠` | [google-agent/QC-系統客製化電子化工廠](https://github.com/shihwei0809/google-agent/tree/main/QC-系統客製化電子化工廠) |
| ├─ `三合一單-to-PHP-Migration` | [google-agent/三合一單-to-PHP-Migration](https://github.com/shihwei0809/google-agent/tree/main/三合一單-to-PHP-Migration) |
| ├─ `軟管-Key-Code-管理優化方案` | [google-agent/軟管-Key-Code-管理優化方案](https://github.com/shihwei0809/google-agent/tree/main/軟管-Key-Code-管理優化方案) |
| ├─ `溫度通報` | [google-agent/溫度通報](https://github.com/shihwei0809/google-agent/tree/main/溫度通報) |
| ├─ `grad-trip` | [google-agent/grad-trip](https://github.com/shihwei0809/google-agent/tree/main/grad-trip) |
| ├─ `保養品` | [google-agent/保養品](https://github.com/shihwei0809/google-agent/tree/main/保養品) |
| ├─ `padlet-board` | [google-agent/padlet-board](https://github.com/shihwei0809/google-agent/tree/main/padlet-board) |
| ├─ `ai anget` (Obsidian 知識庫) | [google-agent/ai anget](https://github.com/shihwei0809/google-agent/tree/main/ai anget) |
| ├─ `aigc-music-video-hub` | [google-agent/aigc-music-video-hub](https://github.com/shihwei0809/google-agent/tree/main/aigc-music-video-hub) |
| ├─ 員工教育訓練測驗系統 (hr_quiz_v2) | 第二類 | [google-agent/影片生成/hr_quiz_v2](https://github.com/shihwei0809/google-agent/tree/main/影片生成/hr_quiz_v2) |
| **`C:\GOOGLE ANGET\AI 克隆聲音`** | [shihwei0809/voxcpm2-voice-cloner](https://github.com/shihwei0809/voxcpm2-voice-cloner) |
| **`C:\GOOGLE ANGET\Google Classroom anget`** | [mathruffian-dot/classroom-agent-kit](https://github.com/mathruffian-dot/classroom-agent-kit) |
| **`C:\GOOGLE ANGET\clasp-netlify-mcp-guide`** | [mathruffian-dot/clasp-netlify-mcp-guide](https://github.com/mathruffian-dot/clasp-netlify-mcp-guide) |
| **`C:\GOOGLE ANGET\claude-html-slide-builder`** | [mathruffian-dot/claude-html-slide-builder](https://github.com/mathruffian-dot/claude-html-slide-builder) |
| **`C:\GOOGLE ANGET\claude-video-specs`** | [mathruffian-dot/claude-video-specs](https://github.com/mathruffian-dot/claude-video-specs) |

---

## 🤖 給 AI Agent 的重要規範與同步機制
為防止本機專案與說明書、紀錄檔脫節，**所有 AI Coding Agent 在此電腦上執行工作時必須遵守以下協議**：
1. **建立/變更專案後**：必須在 `說明書/` 對應目錄下建立或更新該專案的 Markdown 操作說明書。
2. **更新說明書主入口**：必須在 `C:\GOOGLE ANGET\說明書\index.html` 的 `manualsData` 陣列中新增/更新該說明書之內容（需使用腳本進行 JSON 序列化，防止轉義錯誤），並同步更新 `說明書/README.md`。
3. **更新專案紀錄檔**：在 `C:\GOOGLE ANGET\PROJECT_RECORDS.md`（本檔）中追加新專案之名稱、用途與技術棧，並更新最後修改時間。
4. **雲端同步發佈**：完成上述文件修改後，執行 `netlify deploy --dir=說明書 --prod` 將說明書同步至線上託管空間 (https://cerulean-praline-6b314d.netlify.app/)。

---
*最後更新時間：2026年06月24日*


