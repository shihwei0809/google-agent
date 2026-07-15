from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.schemas import AIRequest, AIResponse
from app.services import ai_service

# ==========================================
# 1. 生命週期管理 (Lifespan)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理 API 伺服器的生命週期。
    在伺服器「啟動前」載入 AI 模型，在「關閉前」進行清理。
    """
    # 啟動時：加載模型
    ai_service.load_model()
    yield
    # 關閉時：清除/釋放模型記憶體
    print(">>> 正在關閉 API 伺服器，釋放 AI 模型資源...")
    ai_service.model = None
    ai_service.is_loaded = False

# ==========================================
# 2. 初始化 FastAPI 應用程式
# ==========================================
app = FastAPI(
    title="公司內部 AI 預測服務 API",
    description="本專案為公司內部 AI 服務的後端 API 範本，支援輸入與輸出驗證、模型啟動加載，並自動生成互動式 Swagger 文件。",
    version="1.0.0",
    lifespan=lifespan
)

# ==========================================
# 3. 設定跨來源資源共享 (CORS) 中介軟體
# ==========================================
# 允許前端應用程式跨域請求此 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在正式環境中，建議將此處限制為公司的特定網域
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 動詞 (GET, POST, etc.)
    allow_headers=["*"],  # 允許所有 Headers
)

# ==========================================
# 4. 定義 API 路由 (Endpoints)
# ==========================================

@app.get("/", summary="基本健康檢查")
def read_root():
    """
    提供簡單的 API 狀態檢查，確認伺服器運作中。
    """
    return {
        "status": "online",
        "message": "AI API 服務正常運行中",
        "model_loaded": ai_service.is_loaded
    }

@app.post(
    "/api/v1/predict", 
    response_model=AIResponse, 
    summary="執行 AI 文本分析",
    description="傳入 JSON 格式的文字與參數，進行 AI 情感分析與摘要生成。"
)
def predict(request: AIRequest):
    """
    AI 文本預測主路由：
    - 輸入：`AIRequest` (自動驗證參數)
    - 輸出：`AIResponse` (自動序列化並輸出)
    """
    try:
        # 呼叫 AI 服務進行處理
        sentiment, confidence, summary, proc_time = ai_service.predict(
            text=request.text,
            temperature=request.temperature
        )
        
        # 回傳符合輸出 Schema 的結構
        return AIResponse(
            success=True,
            input_text=request.text,
            sentiment=sentiment,
            confidence=confidence,
            summary=summary,
            processing_time_ms=proc_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"系統處理錯誤: {str(e)}"
        )
