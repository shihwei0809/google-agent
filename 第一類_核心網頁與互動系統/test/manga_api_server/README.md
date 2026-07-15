# 漫畫專案故事與語音合成 API (Manga API Server)

本目錄為獨立的 API 服務，專為您的漫畫網頁專案（讀取故事 `story.json` 與動態語音合成）設計。

---

## 📂 專案結構

```text
manga_api_server/
├── README.md               # 本專案說明文件
├── requirements.txt        # 依賴套件 (fastapi, uvicorn, pydantic, edge-tts)
├── run_manga_api.bat       # 一鍵啟動批次檔 (運行於 Port 8001)
└── app/
    ├── __init__.py
    └── main.py             # API 核心路由與 edge-tts 合成邏輯
```

---

## 🛠️ API 路由清單 (Endpoints)

### 1. `GET /api/v1/story`
* **功能**：動態讀取專案根目錄的 [story.json](file:///d:/GOOGLE%20ANGET/test/story.json)。
* **前端整合建議**：修改網頁前端的 JS 載入邏輯，改由從此 API 端點拉取 JSON，實現動態編輯故事。

### 2. `POST /api/v1/generate-speech`
* **功能**：接收單句對白，即時調用 `edge-tts` 與您的角色語音/音調參數進行高品質語音合成，並將生成好的 MP3 存回專案的 `assets/audio/` 資料夾下。
* **請求格式 (JSON)**：
  ```json
  {
    "text": "耶！大阪我們來了！第一站先去哪裡？",
    "speaker": "sakura",
    "dialogue_id": "p1_p1_d1"
  }
  ```

---

## 🚀 快速開始

### 雙擊啟動
直接雙擊執行目錄下的 **[run_manga_api.bat](file:///d:/GOOGLE%20ANGET/test/manga_api_server/run_manga_api.bat)** 即可。

* **說明**：
  * 本服務運行於 **Port 8001**（避免與您的測試 API 伺服器衝突）。
  * 啟動後，可在瀏覽器打開 **[http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)** 來使用 Swagger UI 直接進行語音合成測試。
