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
├── auto_upload_flow.py                              # Playwright CDP 接管本機 Chrome 自動上傳 CLI
├── run_server.py                                    # 含 Port Fallback 與 /api/upload-flow 本地伺服器
├── index.html                                       # 3D 智慧儲位數位孿生互動網頁
├── fpv_studio.html                                  # 3D 白模 FPV 運鏡工作室網頁
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
2. **一鍵啟動網頁 3D 雙看板**：
   - 直接雙擊 **`啟動3D儲位展示.bat`**
   - 瀏覽器會自動開啟 `http://localhost:8088/index.html`（並可切換至 `/fpv_studio.html`），同時在終端機顯示區網 IP 供手機預覽。
3. **免 API Key 一鍵自動上傳至 Google Flow**：
   - 直接雙擊 **`一鍵自動上傳Google_Flow.bat`**（或在 `fpv_studio.html` 點擊「🚀 一鍵自動送進 Flow」），會透過本機 Chrome (`Port 9222`) 自動切換成 `影片 -> 影格`、上傳首尾幀並填入 Prompt（使用你帳號的 PRO / 免費點數）。
4. **進階：用 Antigravity 遙控 Blender**：
   - 打開任意 `.blend` 檔 → 按 `N` 鍵叫出側邊欄 → 點選 `MCP for Blender` → 點擊 **Connect to MCP server**，即可直接用中文在 Antigravity 下指令改模型！
