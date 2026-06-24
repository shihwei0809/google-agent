# Claude Video Specs 影片規格與技能指南 (claude-video-specs) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent](https://github.com/shihwei0809/google-agent)


## 專案簡介
本專案為 **三類影片製作規範與 AI Agent 自動化技能建置流程**。它為創作者與 AI Agent（如 Antigravity, Claude Code）定義了標準的影片製作流程與視覺設計依據，並提供自動化安裝與打包腳本，能將影片規格打包成 AI Agent 可直接呼叫的獨立「技能（Skill）」。

## 主要功能特色
- **三類影片規範核心**：
  * **01-活動紀錄影片** (60-180秒)：口白、大字卡與 BGM 過場。
  * **02-教學影片** (4-8分鐘)：SOIL 教學脈絡、動畫與 Edge-TTS。
  * **03-社群科普影片** (2-3分鐘)：強 Hook、多版面與照片佐證。
- **設計理論依據**：引進**李俊儀教授之 SOIL 教學心法**與**林長揚簡報 30 原則**（包括黃金字級階梯 55/34/21/13，以及預設下載源石黑體字型）。
- **Agent 自動化整合 (Bootstrap)**：提供 5 階段流程（環境檢查、字體安裝、動畫設定、渲染打包），使 AI Agent 能夠遵循規範一鍵產出網頁簡報並錄製成影片。

## 技術棧
- **規範排版**：Reveal.js / Reveal-HTML 視覺化簡報
- **自動化指令**：Bash / Python 雙平台腳本
- **技能打包**：JSON / Agent Skills 整合工具

## 專案結構
- `specs/`：三類影片製作規範 Markdown 檔與視覺化版 HTML。
- `examples/`：可直接複製使用的 HTML 動畫範本。
- `install/`：包含環境檢查、源石黑體字體自動下載安裝、技能打包等腳本。
  * `check_env.sh` / `setup.py`：環境檢查工具。
  * `install_fonts.sh`：自動下載並安裝源石黑體。
  * `pack_skill.sh`：將影片專案打包成 Agent 專屬 Skills。
- `opencode.json`：OpenCode Agent 的引導設定檔。

## 本機執行與操作
1. **一鍵安裝環境與字體**：
   在 PowerShell 執行以下命令自動配置：
   ```powershell
   powershell -ExecutionPolicy Bypass -File install/install_all.ps1
   ```
   *(或使用 Python：`python install/setup.py all`)*

2. **啟動影片專案製作**：
   對著 AI 代理（如 Antigravity）下指令：「請啟動 `claude-video-specs` 並為我製作一個 02 類型的教學影片」。Agent 會讀取規範並引導進行。

3. **打包影片專案為 Agent 技能**：
   執行以下命令，將影片專案編譯打包為獨立 Skill（例如以 Reveal.js 生成 Reveal-Slide 技能）：
   ```bash
   python install/setup.py pack my-video 02 --target=antigravity
   ```
