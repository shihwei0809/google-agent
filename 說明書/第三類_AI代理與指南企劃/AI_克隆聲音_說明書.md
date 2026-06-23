# AI 克隆聲音 (AI-Voice-Cloning) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent](https://github.com/shihwei0809/google-agent)


## 專案簡介
本專案為基於 **VoxCPM2** 語音克隆模型所開發的本機語音生成與 Agent 工具包。它能夠克隆使用者或指定角色的音色與語調，並將任意文字轉換為該角色的語音輸出。本系統具備全自動硬體加速偵測，且深度整合了 AI Agent，讓使用者能透過自然語言指令直接呼叫進行語音生成與對話合成。

## 主要功能特色
- **自動偵測 GPU 加速**：自動偵測本機硬體，智慧切換於 NVIDIA GPU (CUDA)、Intel Arc GPU (XPU) 與純 CPU 模式之間。
- **精準語調克隆 (Ultimate Cloning)**：同時使用參考音檔與錄音逐字稿，保留原始音色的呼吸節奏與語氣起伏。
- **網頁錄音 WebUI**：提供極簡網頁錄音介面，使用者可命名角色、看稿朗讀並一鍵錄製與儲存參考音色。
- **Agent 自然語言對接**：深度整合 AI 代理人，支援「用王老師的聲音說...」等自然語言指令，由 Agent 自動在背景執行腳本並回傳音檔。

## 技術棧
- **核心模型**：VoxCPM2 (OpenBMB)
- **開發語言**：Python 3.10–3.12 (以 uv 管理本機虛擬環境)
- **前端介面**：Gradio (WebUI)
- **硬體加速**：PyTorch (CUDA / Intel IPEX / CPU)

## 專案結構
- `app.py` / `webui_record.py`：網頁版語音錄製 UI 程式。
- `clone.py`：單人克隆語音生成工具。
- `dialogue.py`：多人對話克隆語音生成工具。
- `record.py`：本機命令列錄音備用程式。
- `voices/`：存放已錄製的角色聲音目錄（如 `voices/王老師/ref_voice.wav`）。
- `output/`：存放生成的語音檔（.wav）。
- `install.bat` / `start.bat`：一鍵安裝與一鍵啟動錄音 UI 的批次檔。

## 本機執行與操作
1. **一鍵安裝**：
   雙擊 `install.bat`，系統會自動偵測顯卡、建立虛擬環境並安裝所有依賴套件。

2. **錄製音色 (WebUI)**：
   雙擊 `start.bat`，瀏覽器會自動開啟錄音介面。
   * 輸入聲音名稱（如 `王老師`）。
   * 點選「錄音」對著麥克風念出畫面上的逐字稿。
   * 錄完點選「儲存」，音色會自動儲存於 `voices/王老師/` 中。

3. **生成克隆語音**：
   在虛擬環境下執行：
   ```bash
   python clone.py "要生成的文字內容" --voice 王老師
   ```
   產出音檔將存於 `output/cloned_voice.wav`。
   *(或者直接告訴 AI 代理人：「用王老師的聲音說同學們早安，我們開始上課」即可自動生成)*

4. **多人對話生成**：
   編輯 `dialogue.py` 中的對話內容清單，然後執行：
   ```bash
   python dialogue.py
   ```
   將會在 `output/` 下生成雙人對話的音訊檔案。
