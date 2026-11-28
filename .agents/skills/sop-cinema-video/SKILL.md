---
name: sop-cinema-video
description: 企業 SOP 微電影化與混合雙軌教學影片技能。整合路線 B（推薦：Google Flow Agent 真人主角微電影過場 × 實務截圖混剪）、路線 A（全 Flow 電影宣導片）與免費 Google Colab T4 GPU 語音克隆（BreezyVoice 台灣國語 / VoxCPM2 48kHz / Gemini TTS / Edge-TTS）。
---

# 🎬 Enterprise SOP Cinema Video & Colab T4 Voice Cloning (`sop-cinema-video`)

將公司 Word / PDF SOP（或口述主題）升級為「電影級微電影過場 × 零退件實務教學影片」，並內建免手動設定的 **免費 Google Colab T4 雙引擎語音克隆工作站**。

---

## 一、快速參數分流

| 參數 | 選項 | 說明 |
|---|---|---|
| `mode` | **`B`（預設推薦）** | **真人主角微電影過場 × 會計驗證實務畫面混剪**。用 Google Flow Agent 生 3 段關鍵劇情過場（開場 / 痛點反轉 / 結尾交件，360p 合計僅 30 點），中間無縫穿插 Lanczos 銳化真實系統截圖與聚光燈提醒卡。 |
| | `A` | **全 Flow 微電影概念宣導片**（5–6 段全 AI 真人主角劇情，360p 約 50–60 點，下載自動升頻 720p），適合大廳宣傳、對外展示或行前導覽。 |
| `voice` | **`colab-breezy`（真人克隆）** | 免費 Colab T4 跑聯發科＋台大 **BreezyVoice**（Apache-2.0 可商用），上傳 6–10 秒 `ref.wav`，台灣國語最道地，支援注音糾音（`連假[:ㄐㄧㄚ4]`）。 |
| | **`colab-prompt-relay`（免錄音推薦）** | 免費 Colab T4 模式 2：**VoxCPM2 (Apache-2.0)** 先依中文 Prompt 生成 6–8 秒虛擬講師定妝音 `virtual_ref.wav`，自動釋放顯存後交給 **聯發科 BreezyVoice** 跑全片（100% 可商用＋免錄音＋全片音色鎖死不飄）。 |
| | **`colab-voxcpm2`** | 免費 Colab T4 跑 OpenBMB **VoxCPM2**（Apache-2.0，48kHz 超高音質），支援克隆或純文字 Prompt 捏聲。 |
| | **`gemini`** | 呼叫 Gemini TTS API（Rule 10 模型降級鏈 `3.8 -> 3.7 -> 3.6 -> 2.5`，讀取環境變數 `GEMINI_API_KEY`）。 |
| | **`edge`（預設保底）** | 本機零 GPU 秒出 `edge-tts` 台灣女聲（1.0x / 1.2x）。 |
| `flow` | **`agent`（推薦）** | 產出「主角三視圖定妝照＋150–200 字長篇中文首尾幀／運鏡＋海報封面／封底＋BGM」指令包，一鍵貼入 `flow.google.com` Agent 模式。 |
| | **`cdp`** | 透過 `auto_upload_flow.py` 自動接管本機 Chrome (Port 9222)，支援 `--model omni12 --res 360p` 省點自動送件。 |

---

## 二、標準執行流程（從任何專案目錄或 SOP `.docx` 開始）

### Step 1｜匯出台灣讀音正規化配音工作單 (`voice_jobs.json`)
系統會自動把 `A05 → A零五`、`T01 → T零一`、`eTag → 一Tag`、`BPM → B P M`、數字轉國字，避免開源 TTS 中英混讀破音：
```powershell
python build_bpm_sop_video.py --export-voice-jobs
# 方案 A (6 鏡概念片) 也可匯出：
python build_bpm_plan_c_video.py --export-voice-jobs
```

### Step 2｜免費 Google Colab T4 一鍵克隆真人聲音（二選一，一般人員零設定）
- **方式 1（免費 Web 版，一般同事最推薦）**：
  - 雙擊 `blender_3d_demo\一鍵開啟Colab_T4配音工作站.bat`，或開啟：
    `templates/colab_t4_voice_clone.ipynb`
  - 右上角切到 `T4 GPU` → 第 1 格 `VOICE_MODE` 三選一（全 Apache-2.0 可商用）：`1_真人克隆_聯發科BreezyVoice`（需 `ref.wav`）、`2_Prompt捏聲接力_聯發科BreezyVoice`（免錄音，先用 VoxCPM2 捏定妝音再交給 BreezyVoice 鎖聲跑全片）或 `3_純Prompt或克隆_VoxCPM2_48kHz` → `執行階段 -> 全部執行`。
  - 自動完成：建立隔離 venv → T4 批次生 3 個 seed → Whisper 自動驗字挑出 0 錯字音檔 → 去靜音＋響度標準化 `-16 LUFS` → 自動下載 `cloned_audio_ready.zip`。
  - 解壓將 `final_audio/*.mp3` 覆蓋放入目標專案的 `audio/`（例如 `bpm_sop/audio/`）。
- **方式 2（Colab CLI 自動化，適合進階或有算力帳號）**：
  ```powershell
  python ".agents\skills\sop-cinema-video\scripts\colab_t4_voice.py" run `
    --engine breezyvoice `
    --jobs "blender_3d_demo\bpm_sop\bpm_voice_jobs.json" `
    --ref "path\to\ref.wav" `
    --out-dir "blender_3d_demo\bpm_sop\audio"
  ```

### Step 3｜Google Flow Agent 生片（Omni 1.2 Flash 360p 省點法則）
1. 開啟 `https://flow.google.com/` 切換為 **Agent 模式**、模型選 **Omni 1.2 Flash**、解析度選 **360p**（10 秒僅 **10 點**，下載時免費提升至 720p；**免費帳每天 50 點即可跑完路線 B 全部 3 鏡**）。
2. 貼上專案內的 `*_Flow_Agent_電影混剪指令包.md`（先產主角正/側/背定妝照，再依序生 `p0X-1` 首幀、`p0X-2` 尾幀、`v0X` 影片與 `封面`/`封底`）。
3. 若要用瀏覽器自動接管上傳，執行：
   ```powershell
   python auto_upload_flow.py --theme bpm_route_b --model omni12 --res 360p
   ```
4. 將下載的影片與素材放入對應位置：
   - 路線 B 實片：`bpm_sop/flow_clips/b01_intro_flow.mp4`、`b02_bridge_flow.mp4`、`b03_outro_flow.mp4`
   - 電影海報與音樂（選填）：`bpm_sop/flow_frames/cover.png`、`ending.png`、`bpm_sop/bgm.mp3`

### Step 4｜一鍵合成電影級 1080p 成片（自動封面/封底＋`xfade` 柔順轉場＋BGM 自動閃避）
```powershell
# 路線 B：微電影過場 × 會計驗證實務混剪終極版（推薦）
python build_bpm_sop_video.py --cinema --speed 1.2

# 路線 A：方案 C 全 Flow 電影版
python build_bpm_plan_c_video.py
```

---

## 三、核心共用資源位置
- 電影後製共用模組：`.agents/skills/sop-cinema-video/scripts/cinema_post_engine.py`
- Colab T4 CLI 工具：`.agents/skills/sop-cinema-video/scripts/colab_t4_voice.py`
- Colab T4 免費版語音工作站 Notebook：`.agents/skills/sop-cinema-video/templates/colab_t4_voice_clone.ipynb`
- Colab 商用劇情短片工作站 Notebook（Wan 2.2 Apache-2.0＋NT$50 自動停機煞車）：`.agents/skills/sop-cinema-video/templates/colab_wan22_sop_cinema.ipynb`
- Flow Agent 與省點公式：`.agents/skills/sop-cinema-video/references/flow_agent_formula.md`
- 企業實務混剪防呆規範：`.agents/skills/sop-cinema-video/references/sop_hybrid_rules.md`
- Gemini 網頁版可直接匯入之 Skill 包：`.agents/skills/sop-cinema-video/sop-cinema-video-gemini.zip`
