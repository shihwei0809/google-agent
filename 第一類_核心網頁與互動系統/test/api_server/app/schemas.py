from pydantic import BaseModel, Field
from typing import Optional

class AIRequest(BaseModel):
    """
    API 輸入格式定義 (Input Schema)
    使用 Pydantic 進行自動欄位驗證
    """
    text: str = Field(
        ..., 
        min_length=5, 
        description="要給 AI 分析的文本內容，最少 5 個字",
        examples=["這是一個測試用的公司 API 系統，運作非常正常。"]
    )
    max_length: Optional[int] = Field(
        default=100, 
        ge=10, 
        le=500, 
        description="AI 生成的最大字數限制 (10 ~ 500)",
        examples=[100]
    )
    temperature: Optional[float] = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="AI 隨機度 (0.0 到 1.0)，數值越高越有創意，越低越穩定",
        examples=[0.7]
    )

class AIResponse(BaseModel):
    """
    API 輸出格式定義 (Output Schema)
    定義回傳給前端的 JSON 結構
    """
    success: bool = Field(..., description="API 執行狀態是否成功")
    input_text: str = Field(..., description="原始輸入的文字")
    sentiment: str = Field(..., description="AI 分析的情感結果 (正面/中立/負面)")
    confidence: float = Field(..., description="AI 預測的信心指數 (0.0 ~ 1.0)")
    summary: str = Field(..., description="AI 產生的摘要")
    processing_time_ms: float = Field(..., description="AI 模型處理所花費的時間 (毫秒)")
