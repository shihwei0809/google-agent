# AI 影音自動剪輯工作站 (IG Reels & Shorts Auto Generator)

讓使用者上傳素材（影片或圖片）並輸入文案，由 AI 自動進行中文配音、排版設計、裁切為 9:16 直式短影音並壓製輸出 MP4。

## 🌟 核心功能亮點
- **素材智能自適應**：上傳任意尺寸橫式/直式影片或圖片，自動進行 9:16 構圖與慢速推鏡（Ken Burns Effect）。
- **自然中文配音**：整合微軟 Edge-TTS 雲哲男聲與曉臻女聲，免 GPU 零成本生成高清旁白。
- **動態字卡排版**：自動折行、半透明玻璃質感底框、重點霓虹色 Accent Bar 與標題膠囊。
- **一鍵啟動與區網預覽**：提供現代化 Web 控制台，並自動顯示本機與區網 IP，手機或同事可直接開網頁使用。

## 📁 完整檔案結構
```text
C:\GOOGLE ANGET\AI影音自動剪輯工作站\
├── main.py                     # FastAPI 伺服器與 API 端點
├── video_generator.py          # 核心影片合成引擎 (FFmpeg + Edge-TTS + PIL)
├── requirements.txt            # Python 依賴清單
├── 啟動AI影音剪輯工作站.bat     # 一鍵環境偵測、套件安裝、Port切換與開啟瀏覽器
├── setup_env.ps1               # PowerShell 一鍵安裝腳本
├── SKILL.md                    # 給 AI 助理閱讀的操作說明
├── README.md                   # 專案說明書
├── templates/
│   └── index.html              # 互動式 Web 操作介面 (TailwindCSS + 實時播放器)
├── static/                     # 靜態資源目錄
├── uploads/                    # 使用者上傳素材暫存
└── outputs/                    # 輸出之 9:16 MP4 短影音
```

## 🚀 跨電腦一鍵啟動步驟
1. 雙擊執行 `啟動AI影音剪輯工作站.bat`。
2. 系統會自動檢查 Python、安裝缺失套件、切換可用 Port 並於 2 秒後自動在瀏覽器開啟 `http://localhost:8050`。
