# AI 教育訓練平台 (AI-Assisted Training Platform)

## 專案簡介
這是一個結合 AI 助理的教育訓練平台。使用者可以在平台上瀏覽教育訓練教材，並透過內建的 AI 助理即時提問，AI 會根據教材內容或領域知識提供解答，大幅提升學習效率與自主學習體驗。

## 核心功能列表
*   **教材閱覽系統**：支援 Markdown/PDF 等格式的教材展示。
*   **AI 智能助教**：整合 Gemini API 的對話視窗，支援上下文記憶與教材內容檢索 (RAG)。
*   **QA 歷史紀錄**：自動保存使用者的提問紀錄，方便日後複習。
*   **一鍵部署**：透過標準化腳本快速啟動前端與後端服務。

## 完整檔案結構說明
```
教育訓練-C0588-教材/
├── README.md               # 專案說明文件
├── SKILL.md                # AI 代理技能與任務指引
├── setup_env.ps1           # 一鍵環境安裝腳本
├── build_manual_doc.py     # 操作手冊自動生成腳本
├── backend/                # FastAPI 後端 API 服務
│   ├── main.py             # 後端程式進入點
│   ├── requirements.txt    # Python 依賴清單
│   └── .env                # 環境變數 (API Key 等)
└── frontend/               # React 前端介面
    ├── package.json        # 前端套件清單
    ├── vite.config.js      # Vite 設定檔
    └── src/                # 前端原始碼
```

## 快速啟動與部署步驟
1. 確保已安裝 Node.js 與 Python 3.10+。
2. 執行 `./setup_env.ps1` 進行環境初始化與套件安裝。
3. 啟動後端：`cd backend && uvicorn main:app --reload --port 8000`
4. 啟動前端：`cd frontend && npm run dev`
5. 打開瀏覽器訪問前端網址即可開始使用。
