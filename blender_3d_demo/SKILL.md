---
name: blender-3d-demo
description: Blender 5.3 + Blender MCP + Three.js Web 3D 數位孿生倉庫與 AI 影片白模 FPV 運鏡工作室專案指引。
---

# 🧊 Blender 3D AI 自動建模與 FPV 白模運鏡工作室 (SKILL)

## 1. 專案資訊與環境需求
- **專案目錄**：`blender_3d_demo/`
- **核心依賴**：
  - **Python 3.9+**（套件：`python-docx`、`pillow`、`playwright`、`edge-tts`、`imageio-ffmpeg`）
  - **FFmpeg**（系統 `ffmpeg` 或 `imageio-ffmpeg` 內建二進位檔，用於 1080p 分鏡合成）
  - **Blender 5.3+**（預設安裝路徑：`C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`）
  - **Astral `uv` / `uvx`**（路徑：`%USERPROFILE%\.local\bin\uvx.exe`，用於執行 `blender-mcp`）
  - **Antigravity MCP 設定**：`~/.gemini/config/mcp_config.json` 需註冊 `"blender"` server。

## 2. AI 助理引導規範
1. 若本機尚未安裝 `Blender`、`uvx`、`python-docx` 或 `playwright`，請先引導使用者執行：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup_env.ps1
   ```
2. 若使用者要求無頭（不開視窗、免獨顯負擔）重新生成 3D 場景或白模影片，直接呼叫 Blender CLI：
   - 重新生成 3D 倉庫模型：
     ```powershell
     & "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P generate_warehouse_3d.py
     ```
   - 重新算圖輸出 FPV 白模影片 (`fpv_white_model.mp4`) 與首尾幀：
     ```powershell
     & "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P generate_fpv_white_model.py
     ```
3. 啟動本機 3D 展示網頁伺服器（自動偵測 Port Fallback 起始 `8088`）：
   ```powershell
   python run_server.py
   ```
   或直接執行 `啟動3D儲位展示.bat`。
4. 免 API Key 一鍵自動上傳至本機 Chrome Google Flow（支援 `kids` / `cyberpunk` / `wuxia` / `white` / `bpm_shot01` / `bpm_shot05` / `bpm_shot08` / `bpm_all` / `bpm_route_b`；預設 `Omni 1.2 Flash + 360p` 省點模式）：
   ```powershell
   python auto_upload_flow.py --theme kids
   python auto_upload_flow.py --theme bpm_route_b --model omni12 --res 360p
   ```
   或直接雙擊 `一鍵自動上傳Google_Flow.bat`。
5. 一鍵從 `..\BPM一般費用報銷單_私車公用操作流程.docx` 抽圖、配音並合成 1080p 教學總片（支援 `--voice hsiaochen|yunjhe|hsiaoyu|duet`、路線 B 電影混剪 `--cinema`、匯出 Colab 配音單 `--export-voice-jobs`）：
   ```powershell
   python build_bpm_sop_video.py --rebuild-audio --voice hsiaochen
   python build_bpm_sop_video.py --export-voice-jobs
   python build_bpm_sop_video.py --cinema --speed 1.2
   python build_bpm_plan_c_video.py --rebuild-audio --voice hsiaochen
   ```
6. 免費 Google Colab T4 雙引擎語音克隆（BreezyVoice 台灣國語 / VoxCPM2 48kHz）：
   - 雙擊 `一鍵開啟Colab_T4配音工作站.bat`（或手動上傳 `..\.agents\skills\sop-cinema-video\templates\colab_t4_voice_clone.ipynb` 至 Colab 切換 `T4 GPU`）。
   - 詳見通用技能：`..\.agents\skills\sop-cinema-video\SKILL.md` 與 `bpm_sop\BPM_Flow_Agent_電影混剪指令包.md`。
7. 更新功能或圖檔後，同步重新生成圖文操作手冊：
   ```powershell
   python build_manual_doc.py
   ```
