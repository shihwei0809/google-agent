# 公司內部 AI 預測服務 API 範本

本專案使用 **Python (FastAPI)** 框架實作，專為需要串接 AI 模型的 API 設計。具備自動輸入/輸出驗證、模型預載入（Lifespan）及自動生成 API 文件的特點。

---

## 📂 專案目錄結構

```text
api_server/
├── README.md               # 本專案說明文件
├── requirements.txt        # 依賴套件清單 (fastapi, uvicorn, pydantic)
└── app/
    ├── __init__.py
    ├── main.py             # API 主程式 (包含路由與 CORS 設定)
    ├── schemas.py          # 定義輸入 (AIRequest) 與輸出 (AIResponse) 的格式
    └── services.py         # AI 服務層 (模擬模型載入與推論運算)
```

---

## 🚀 快速開始指南

### 1. 建立虛擬環境與安裝依賴 (建議)

在終端機中，切換到 `api_server` 目錄並安裝套件：

```bash
# 1. 切換目錄
cd api_server

# 2. 建立虛擬環境 (可選但推薦)
python -m venv venv

# 3. 啟用虛擬環境
# Windows Powershell:
.\venv\Scripts\Activate.ps1
# Mac / Linux:
source venv/bin/activate

# 4. 安裝依賴套件
pip install -r requirements.txt
```

### 2. 啟動 API 伺服器

執行以下指令啟動 FastAPI 開發伺服器：

```bash
uvicorn app.main:app --reload
```

* **`app.main:app`**：代表讀取 `app` 資料夾下 `main.py` 裡的 `app` 實例。
* **`--reload`**：開發模式，程式碼有變更時會自動重新載入伺服器。

---

## 🔍 如何測試與使用

### 1. 互動式 API 文件 (Swagger UI)
伺服器啟動後，請在瀏覽器打開：
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

您可以在此處看見所有的 API 路由。點擊 **`POST /api/v1/predict`** -> **"Try it out"**，便可以直接在瀏覽器上傳送測試資料並觀看即時回傳的結果。

### 2. 替代文件 (ReDoc)
若喜歡另一種風格的靜態文件，可以瀏覽：
👉 **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)**

---

## 🛠️ 如何在此專案擴充

1. **修改輸入/輸出欄位**：
   * 前往 [app/schemas.py](file:///d:/GOOGLE%20ANGET/test/api_server/app/schemas.py)。
   * 修改 `AIRequest`（輸入）或 `AIResponse`（輸出）的欄位定義。

2. **串接您的真實 AI 模型**：
   * 前往 [app/services.py](file:///d:/GOOGLE%20ANGET/test/api_server/app/services.py)。
   * 修改 `load_model` 方法來載入您訓練好的模型（如 `.h5`, `.pt`, 或是 HuggingFace 管道）。
   * 修改 `predict` 方法，將傳入的 `text` 送入您的模型推論，並將模型輸出結果回傳。
