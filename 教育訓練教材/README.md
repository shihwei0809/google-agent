# AI 教育訓練平台 (AI-Assisted Training Platform)

## 🌟 專案簡介
這是一個結合 AI 輔助的教育訓練平台。使用者可以在網頁上傳教育訓練教材，並透過內建的 AI 助理進行摘要、AI 語音朗讀與測驗生成，大幅提升學習效率與自主學習力。

## ✨ 核心功能
*   **教材整合**：支援 Markdown/PDF 格式教材匯入。
*   **AI 助理**：結合 Gemini API，支援上下文記憶與教材問答 (RAG)。
*   **QC 系統與提案改善**：內建 QC 系統提案改善書與人工流程電子化管理。
*   **PWA 雙軌架構與自動化部署**：全面升級 PWA 離線支援與 App 安裝模式，並支援 Cloudflare D1 雲端資料庫一鍵部署！

## 📂 檔案結構
`
教育訓練教材/
├── README.md               # 本專案說明
├── SKILL.md                # AI 代理操作與環境引導
├── setup_env.ps1           # 一鍵安裝環境腳本
├── build_manual_doc.py     # 操作手冊自動生成腳本
├── deliverables/           # 產出物 (操作手冊、QC 提案改善書)
├── 1_Web_網頁版/            # FastAPI 網頁服務核心
└── 2_PWA_App版/             # PWA 離線 App 支援與前端介面
`

## 🚀 快速啟動與環境建置
1. 確認已安裝 Node.js 與 Python 3.10+。
2. 執行 ./setup_env.ps1 進行初始化與套件安裝。
3. **啟動後端**：cd backend && uvicorn main:app --reload --port 8000
4. **啟動前端/PWA**：雙擊 啟動PWA本機測試.bat 或進入 frontend 執行 
pm run dev。
5. 開啟終端機顯示的網址即可開始使用。

## 💡 最新更新 (PWA 與雲端部署)
* **PWA 安裝**：網頁頂部現在會出現「安裝為應用程式」提示，支援手機與電腦版獨立 App 模式。
* **Cloudflare 一鍵上線**：可執行包內的自動部署腳本，無伺服器即可直接上線。
