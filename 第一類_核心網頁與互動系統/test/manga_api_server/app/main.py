import os
import json
import ssl
import edge_tts.communicate
# Bypass SSL verification to avoid ClientConnectorCertificateError in corporate networks
edge_tts.communicate._SSL_CTX = ssl._create_unverified_context()

import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Initialize FastAPI App
app = FastAPI(
    title="漫畫專案故事與語音合成 API 服務",
    description="專為漫畫播放網頁設計的 API，支援讀取 story.json 以及動態調用 edge-tts 生成 Microsoft Neural 語音檔。",
    version="1.0.0"
)

# Enable CORS for frontend connection (port 8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Base Paths (relative to manga_api_server/app/main.py)
# main.py is in manga_api_server/app/
# BASE_DIR should point to the main project directory (d:/GOOGLE ANGET/test/)
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_FILE_DIR))
STORY_PATH = os.path.join(BASE_DIR, "story.json")
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")

# ==========================================
# 1. Pydantic Request Models
# ==========================================
class TTSRequest(BaseModel):
    text: str = Field(..., description="要合成語音的對白文字內容")
    speaker: str = Field(..., description="對白說話者角色名稱 (sakura / taiga / papa / mama)")
    dialogue_id: str = Field(..., description="對白唯一的 ID (用來做檔名，例如: p1_p1_d1)")

# ==========================================
# 2. Endpoints
# ==========================================

@app.get("/", summary="健康檢查")
def read_root():
    return {
        "status": "online",
        "message": "漫畫專案 API 服務正常運行中 (Port 8001)",
        "paths": {
            "story_exists": os.path.exists(STORY_PATH),
            "audio_dir_exists": os.path.exists(AUDIO_DIR)
        }
    }

@app.get("/api/v1/story", summary="讀取故事 JSON 內容")
def get_story():
    """
    動態讀取專案根目錄的 story.json 內容並以 JSON 回傳。
    """
    if not os.path.exists(STORY_PATH):
        raise HTTPException(status_code=404, detail=f"找不到故事檔案，路徑為: {STORY_PATH}")
    try:
        with open(STORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取故事檔案失敗: {str(e)}")

@app.post("/api/v1/generate-speech", summary="動態生成 Neural 語音檔 (edge-tts)")
async def generate_speech(request: TTSRequest):
    """
    接收對白與角色資訊，動態在後台執行 edge-tts 合成高品質 Microsoft Neural 語音，
    並直接儲存於專案的 assets/audio/ 目錄下。
    """
    # 角色語音與參數配置 (對應您原本 project 中的 VOICE_MAPPING, RATE_MAPPING, PITCH_MAPPING)
    VOICE_MAPPING = {
        "sakura": "zh-TW-HsiaoChenNeural", # 小妤 (11yo female) - child-like
        "taiga": "zh-TW-YunJheNeural",      # 小融 (10yo male) - pitched up
        "papa": "zh-TW-YunJheNeural",      # 爸爸 - Standard Taiwanese male
        "mama": "zh-TW-HsiaoYuNeural"      # 媽媽 - Standard Taiwanese female
    }
    RATE_MAPPING = {
        "sakura": "+0%",
        "taiga": "+15%", # Faster rate for energetic boy
        "papa": "+0%",
        "mama": "+0%"
    }
    PITCH_MAPPING = {
        "sakura": "+0Hz",
        "taiga": "+35Hz", # Pitch shift up to sound like a boy
        "papa": "+0Hz",
        "mama": "+0Hz"
    }

    speaker = request.speaker.lower()
    voice = VOICE_MAPPING.get(speaker, "zh-TW-HsiaoYuNeural")
    rate = RATE_MAPPING.get(speaker, "+0%")
    pitch = PITCH_MAPPING.get(speaker, "+0Hz")

    # Ensure audio output folder exists
    os.makedirs(AUDIO_DIR, exist_ok=True)
    filename = f"ms_{request.dialogue_id}.mp3"
    output_path = os.path.join(AUDIO_DIR, filename)

    try:
        # Call edge-tts to generate and save
        communicate = edge_tts.Communicate(request.text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)
        
        return {
            "success": True,
            "message": f"成功生成語音檔: {filename}",
            "filename": filename,
            "url_path": f"assets/audio/{filename}",
            "size_bytes": os.path.getsize(output_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"語音生成錯誤: {str(e)}"
        )

@app.put("/api/v1/story", summary="更新並儲存故事 JSON 內容")
def update_story(story_data: dict):
    """
    接收前端編輯後的故事 JSON，直接寫回專案的 story.json 進行保存。
    """
    try:
        with open(STORY_PATH, "w", encoding="utf-8") as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        return {
            "success": True,
            "message": "故事檔案已成功儲存並同步到伺服器！"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"儲存故事檔案失敗: {str(e)}"
        )

