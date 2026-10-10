# 回收液入料記錄系統

這是一個專門用於記錄回收液入料過程的系統，分為「入料前」與「入料後」兩階段，確保資料準確且避免車號重複。

## 核心功能
* **入料前記錄**：拍攝入料前儲槽液位與車輛照片，並輸入車號與日期。
* **狀態暫存**：入料前的資料會暫存於系統，等待入料完成。
* **入料後記錄**：入料完成後，人員可從介面選取剛才的車輛，拍攝入料後的儲槽液位。
* **防呆機制**：透過日期與車號檢查，避免重複登錄。
* **自動上傳/儲存**：完成的資料與照片會自動整理並儲存。

## 檔案結構
```text
回收液入料記錄/
├── 1_Web_網頁版/            # 一般網頁版
├── 2_PWA_App版/             # PWA 獨立 App 版 (FastAPI 後端 + SQLite)
│   ├── main.py              # FastAPI 後端程式
│   ├── static/              # 靜態檔案 (HTML/JS/CSS)
│   │   ├── index.html       # 首頁 (入料前)
│   │   ├── after.html       # 入料後介面
│   │   └── js/              # 前端邏輯
│   ├── data/                # SQLite 資料庫與照片儲存位置
│   └── requirements.txt     # Python 依賴
├── 3_Cloudflare_D1版/       # Cloudflare Pages + D1 版
├── README.md                # 專案說明書
├── SKILL.md                 # AI 代理技能與說明
└── setup_env.ps1            # 環境設定腳本
```

## 快速啟動
1. 進入 `2_PWA_App版`
2. 執行 `pip install -r requirements.txt`
3. 執行 `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
