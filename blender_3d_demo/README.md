# 🧊 Blender 3D AI 自動建模與 FPV 白模運鏡工作室 (blender_3d_demo)

整合 **Blender 5.3 + Blender MCP (`uvx blender-mcp`) + Three.js WebGL 數位孿生看板** 的一站式 AI 3D 創作與白模 (Previs) 運鏡系統，針對無獨顯筆電（如 Intel Iris Xe 內顯）最佳化。

---

## ✨ 核心功能亮點

1. **AI 中文遙控 Blender 即時建模 (`blender-mcp`)**：
   - 不必記住 Blender 複雜快捷鍵，直接透過 Antigravity + MCP 雙向 Socket 即時生成、上色、打光、匯出 `.glb`。
2. **🏭 3D 智慧倉庫數位孿生看板 (`index.html`)**：
   - 由 `generate_warehouse_3d.py` 自動生成 36 個可點擊儲位 (`Slot_A-01-1` ~ `Slot_C-04-3`) 與巡航 AGV 搬運車 (`AGV_Robot_01`)。
   - 支援 360° 旋轉縮放、關鍵字飛往定位、狀態篩選與網頁端即時切換儲位顏色。
3. **🎬 AI 影片專用 3D 白模 FPV 運鏡工作室 (`fpv_studio.html`)**：
   - 使用 Blender `BLENDER_WORKBENCH` 白模引擎（免獨顯、約 20 秒內算完 120 格 1280×720 H.264 MP4），精準控制 AI 影片運鏡。
   - 支援 **Google Flow (`Frames to Video`)** 首尾幀輸出與 **Seedance / 可靈 Kling / Runway** 影片參考管線。
   - 內建賽博龐克 (Cyberpunk) 與奇幻武俠 (Fantasy Wuxia) 已對齊白模透視的電影級首尾幀圖組與一鍵複製 Prompt。
4. **📑 BPM 一般費用報銷單（私車公用）混合雙軌分鏡工作室 (`bpm_storyboard_studio.html`)**：
   - 由 `build_bpm_sop_video.py` 自動從 `BPM一般費用報銷單_私車公用操作流程.docx` 抽取 11 張高清截圖、生成 3 組 Google Flow 情境首尾幀，並以 `edge-tts` 台灣女聲配音合成 1080p 8 鏡有聲教學總片。
   - **混合雙軌策略（方案 A）**：將 `Shot 01 / 05 / 08` 情境分鏡透過 `auto_upload_flow.py --theme bpm_all` 批次送進 Google Flow（共 90 點）；核心 BPM 表單操作 (`Shot 02, 03, 04, 06, 07`) 由 Python 原圖高清放大＋動態紅框導覽，確保代碼與數字 100% 清晰銳利。
   - **全 Flow 概念動畫版（方案 C）**：由 `build_bpm_plan_c_video.py` 複用上述 3 支 Flow 實片並補齊 `C02 / C03 / C05` 三段 3D 概念分鏡，產出 6 鏡全 Flow 概念總片 (`bpm_sop_plan_c/`)，支援滿版電影字幕、3 秒封面/封底、`0.4s xfade` 轉場與 BGM 自動語音閃避。
   - **路線 B 電影混剪終極版 (`--cinema`) 與免費 Colab T4 語音克隆**：支援整合 `bpm_sop/flow_clips/b01_intro_flow.mp4`、`b02_bridge_flow.mp4`、`b03_outro_flow.mp4` 主角微電影過場，並透過 `一鍵開啟Colab_T4配音工作站.bat` 直接使用免費 Google Colab T4 GPU（可選 **BreezyVoice** 台灣國語或 **VoxCPM2** 48kHz）克隆真人配音。

---

## 📁 完整檔案結構 (File Tree)

```text
blender_3d_demo/
├── README.md                                        # 專案說明書（本文件）
├── SKILL.md                                         # AI 助理指引與執行指令規範
├── setup_env.ps1                                    # 一鍵環境檢測與安裝腳本 (PowerShell)
├── build_manual_doc.py                              # 圖文並茂操作手冊自動生成腳本
├── Blender_3D_AI建模與白模運鏡系統_操作手冊.docx        # 自動生成之圖文 Word 操作手冊
├── 啟動3D儲位展示.bat                                 # 一鍵環境檢查、Port 偵測並啟動展示伺服器
├── 一鍵自動上傳Google_Flow.bat                         # 免 API Key 開啟本機 Chrome 自動上傳首尾幀
├── 一鍵開啟Colab_T4配音工作站.bat                      # 一鍵匯出台灣讀音腳本並開啟免費 Colab T4 克隆配音站
├── auto_upload_flow.py                              # Playwright CDP 接管本機 Chrome 自動上傳 CLI（支援 Omni 1.2 360p 與 bpm_route_b）
├── build_bpm_sop_video.py                           # BPM 報銷單雙軌分鏡／路線 B 電影混剪終極版建置腳本
├── build_bpm_plan_c_video.py                        # BPM 報銷單方案 C 全 Flow 6 鏡電影動畫建置腳本
├── run_server.py                                    # 含 Port Fallback、/api/upload-flow 與 /api/rebuild-bpm-video 伺服器
├── index.html                                       # 3D 智慧儲位數位孿生互動網頁
├── fpv_studio.html                                  # 3D 白模 FPV 運鏡工作室網頁
├── bpm_storyboard_studio.html                       # BPM 報銷單方案 A / 方案 C 分鏡管理與教學播放工作台
├── bpm_sop/                                         # 方案 A & 路線 B 工作目錄（figures / flow_frames / flow_clips / audio / 總片 / BPM_Flow_Agent_電影混剪指令包.md）
├── bpm_sop_plan_c/                                  # 方案 C 工作目錄（flow_frames / new_flow_frames / flow_clips / 總片）
├── generate_warehouse_3d.py                         # Blender 無頭腳本：生成智慧倉庫 .blend / .glb
├── generate_fpv_white_model.py                      # Blender 無頭腳本：算圖輸出 FPV 白模 MP4/首尾幀
├── blender_mcp_addon.py                             # Blender MCP 外掛腳本 (Socket localhost:9876)
├── warehouse_scene.blend                            # Blender 3D 倉庫原始場景檔
├── warehouse_3d.glb                                 # 網頁版 3D 倉庫模型
├── fpv_white_model.blend                            # Blender 白模 FPV 運鏡原始場景檔
├── fpv_white_model.glb                              # 網頁版 3D 白模街道與軌跡模型
├── fpv_white_model.mp4                              # 5 秒 1280x720 24fps 白模 FPV 運鏡影片
├── fpv_camera_path.json                             # 120 幀攝影機座標與轉彎傾角 JSON
├── fpv_first_frame.png                              # 第 1 格高空俯瞰白模首幀圖
├── fpv_last_frame.png                               # 第 120 格主角正面白模尾幀圖
├── cyberpunk_first_frame.png                        # 賽博龐克風格首幀圖 (Google Flow Start)
├── cyberpunk_last_frame.png                         # 賽博龐克風格尾幀圖 (Google Flow End)
├── wuxia_first_frame.png                            # 奇幻武俠風格首幀圖 (Google Flow Start)
├── wuxia_last_frame.png                             # 奇幻武俠風格尾幀圖 (Google Flow End)
├── kids_first_frame.png                             # 兒童卡通版首幀圖 (Google Flow Start)
└── kids_last_frame.png                              # 兒童卡通版尾幀圖 (Google Flow End)
```

---

## 🚀 跨電腦一鍵啟動與安裝步驟

1. **初始化環境（新電腦首次使用執行一次）**：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup_env.ps1
   ```
   *(會自動安裝 `python-docx`、`pillow`、`playwright`、`uv/uvx`、偵測/安裝 Blender 5.3、註冊 Blender MCP 外掛與生成 Word 手冊)*
2. **一鍵啟動網頁 3D 與雙軌分鏡看板**：
   - 直接雙擊 **`啟動3D儲位展示.bat`**
   - 瀏覽器會自動開啟 `http://localhost:8088/index.html`（並可切換至 `/fpv_studio.html` 與 `/bpm_storyboard_studio.html`），同時在終端機顯示區網 IP 供手機預覽。
3. **免 API Key 一鍵自動上傳至 Google Flow**：
   - 直接雙擊 **`一鍵自動上傳Google_Flow.bat`**（或在 `fpv_studio.html` / `bpm_storyboard_studio.html` 點擊一鍵送進 Flow），會透過本機 Chrome (`Port 9222`) 自動切換成 `影片 -> 影格 · 720p · 10 秒 · x 1`、上傳首尾幀並填入 Prompt（支援 `bpm_all` 三鏡批次送出）。
4. **重新生成 BPM 有聲教學總片**：
   - 若將 Google Flow 下載的實片放入 `bpm_sop/flow_clips/`（`shot01_flow.mp4`、`shot05_flow.mp4`、`shot08_flow.mp4`），可於網頁點擊「🔄 重新合成總片」或執行 `python build_bpm_sop_video.py`。
4. **進階：用 Antigravity 遙控 Blender**：
   - 打開任意 `.blend` 檔 → 按 `N` 鍵叫出側邊欄 → 點選 `MCP for Blender` → 點擊 **Connect to MCP server**，即可直接用中文在 Antigravity 下指令改模型！
