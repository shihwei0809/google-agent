import time
import asyncio
from typing import Tuple

class AIService:
    """
    AI 服務類別，負責處理模型加載與推論邏輯。
    在實際應用中，可以將此處替換為加載 PyTorch, TensorFlow 或 HuggingFace 模型。
    """
    def __init__(self):
        self.model = None
        self.is_loaded = False

    def load_model(self):
        """
        模擬模型載入過程。這個步驟通常很耗時且耗記憶體，
        因此只在 API 伺服器啟動時執行一次。
        """
        print(">>> 正在加載 AI 模型與參數...")
        time.sleep(1.5)  # 模擬模型加載耗時 1.5 秒
        self.model = "MockTransformerV1"
        self.is_loaded = True
        print(">>> AI 模型加載完成，系統準備就緒！")

    def predict(self, text: str, temperature: float) -> Tuple[str, float, str, float]:
        """
        執行 AI 推論 (Inference)
        """
        if not self.is_loaded:
            raise RuntimeError("模型尚未加載完成！")
        
        start_time = time.time()
        
        # 模擬 AI 處理延遲 (例如 100ms)
        time.sleep(0.1)
        
        # 簡單的模擬 AI 判斷邏輯
        text_len = len(text)
        
        # 情感判斷
        if "好" in text or "棒" in text or "成功" in text:
            sentiment = "正面 (Positive)"
            confidence = 0.95
        elif "差" in text or "壞" in text or "失敗" in text or "錯" in text:
            sentiment = "負面 (Negative)"
            confidence = 0.88
        else:
            sentiment = "中立 (Neutral)"
            confidence = 0.75
            
        summary = f"【AI 摘要】輸入文字共 {text_len} 字。分析判斷其情緒為 {sentiment}。"
        
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000
        
        return sentiment, confidence, summary, round(processing_time_ms, 2)

# 實例化為單例 (Singleton)，供 API 路由共用
ai_service = AIService()
