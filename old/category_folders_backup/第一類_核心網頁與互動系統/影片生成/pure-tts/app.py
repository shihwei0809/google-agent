import os
import glob
import json
import uuid
import socket
import logging
import base64
import requests
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse
import edge_tts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pure-tts")

app = FastAPI(title="Pure TTS Generator")

BASE_DIR = Path(__file__).parent.resolve()
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Voice Groups (Identical to pdf-to-video) ───
VOICE_GROUPS = {
    "🇹🇼 繁體中文（台灣）": [
        {"id": "zh-TW-HsiaoChenNeural", "label": "曉臻（女聲・自然）"},
        {"id": "zh-TW-HsiaoYuNeural",   "label": "曉雨（女聲・活潑）"},
        {"id": "zh-TW-YunJheNeural",    "label": "雲哲（男聲）"},
    ],
    "🇨🇳 普通話（大陸）": [
        {"id": "zh-CN-XiaoxiaoNeural",  "label": "曉曉（女聲・溫柔）"},
        {"id": "zh-CN-XiaoyiNeural",    "label": "曉伊（女聲・活潑）"},
        {"id": "zh-CN-YunxiNeural",     "label": "雲希（男聲・年輕）"},
        {"id": "zh-CN-YunyangNeural",   "label": "雲揚（男聲・播報）"},
        {"id": "zh-CN-YunjianNeural",   "label": "雲健（男聲・有力）"},
        {"id": "zh-CN-XiaochenNeural",  "label": "曉辰（女聲・專業）"},
    ],
    "🇭🇰 粵語（香港）": [
        {"id": "zh-HK-HiuGaaiNeural",  "label": "曉佳（女聲）"},
        {"id": "zh-HK-HiuMaanNeural",  "label": "曉雯（女聲）"},
        {"id": "zh-HK-WanLungNeural",  "label": "雲龍（男聲）"},
    ],
    "🇺🇸 英文（美國）": [
        {"id": "en-US-JennyNeural",  "label": "Jenny（Female・natural）"},
        {"id": "en-US-AriaNeural",   "label": "Aria（Female・warm）"},
        {"id": "en-US-GuyNeural",    "label": "Guy（Male）"},
        {"id": "en-US-DavisNeural",  "label": "Davis（Male・casual）"},
        {"id": "en-US-TonyNeural",   "label": "Tony（Male・confident）"},
    ],
    "🇬🇧 英文（英國）": [
        {"id": "en-GB-SoniaNeural",  "label": "Sonia（Female）"},
        {"id": "en-GB-RyanNeural",   "label": "Ryan（Male）"},
        {"id": "en-GB-LibbyNeural",  "label": "Libby（Female）"},
    ],
    "🇯🇵 日文": [
        {"id": "ja-JP-NanamiNeural",  "label": "七海（女聲）"},
        {"id": "ja-JP-KeitaNeural",   "label": "圭太（男聲）"},
    ],
    "🇰🇷 韓文": [
        {"id": "ko-KR-SunHiNeural",  "label": "선히（女聲）"},
        {"id": "ko-KR-InJoonNeural", "label": "인준（男聲）"},
    ],
}

# ─── Gemini TTS Voices (Full 30 voices from pdf-to-video) ───
GEMINI_VOICES = [
    {"id": "Zephyr",        "label": "Zephyr",        "style": "Bright"},
    {"id": "Puck",          "label": "Puck",          "style": "Upbeat"},
    {"id": "Charon",        "label": "Charon",        "style": "Informative"},
    {"id": "Kore",          "label": "Kore",          "style": "Firm"},
    {"id": "Fenrir",        "label": "Fenrir",        "style": "Excitable"},
    {"id": "Leda",          "label": "Leda",          "style": "Youthful"},
    {"id": "Orus",          "label": "Orus",          "style": "Firm"},
    {"id": "Aoede",         "label": "Aoede",         "style": "Breezy"},
    {"id": "Callirrhoe",    "label": "Callirrhoe",    "style": "Easy-going"},
    {"id": "Autonoe",       "label": "Autonoe",       "style": "Bright"},
    {"id": "Enceladus",     "label": "Enceladus",     "style": "Breathy"},
    {"id": "Iapetus",       "label": "Iapetus",       "style": "Clear"},
    {"id": "Umbriel",       "label": "Umbriel",       "style": "Easy-going"},
    {"id": "Algieba",       "label": "Algieba",       "style": "Smooth"},
    {"id": "Despina",       "label": "Despina",       "style": "Smooth"},
    {"id": "Erinome",       "label": "Erinome",       "style": "Clear"},
    {"id": "Algenib",       "label": "Algenib",       "style": "Gravelly"},
    {"id": "Rasalgethi",    "label": "Rasalgethi",    "style": "Informative"},
    {"id": "Laomedeia",     "label": "Laomedeia",     "style": "Upbeat"},
    {"id": "Achernar",      "label": "Achernar",      "style": "Soft"},
    {"id": "Alnilam",       "label": "Alnilam",       "style": "Firm"},
    {"id": "Schedar",       "label": "Schedar",       "style": "Even"},
    {"id": "Gacrux",        "label": "Gacrux",        "style": "Mature"},
    {"id": "Pulcherrima",   "label": "Pulcherrima",   "style": "Forward"},
    {"id": "Achird",        "label": "Achird",        "style": "Friendly"},
    {"id": "Zubenelgenubi", "label": "Zubenelgenubi", "style": "Casual"},
    {"id": "Vindemiatrix",  "label": "Vindemiatrix",  "style": "Gentle"},
    {"id": "Sadachbia",     "label": "Sadachbia",     "style": "Lively"},
    {"id": "Sadaltager",    "label": "Sadaltager",    "style": "Knowledgeable"},
    {"id": "Sulafat",       "label": "Sulafat",       "style": "Warm"},
]

GEMINI_MODELS = [
    {"id": "gemini-2.5-flash-preview-tts", "name": "Gemini 2.5 Flash TTS (推薦)"},
    {"id": "gemini-2.5-pro-preview-tts",   "name": "Gemini 2.5 Pro TTS (高品質)"},
    {"id": "gemini-3.1-flash-tts",         "name": "Gemini 3.1 Flash TTS (最新推薦)"},
    {"id": "gemini-3.1-flash-tts-preview", "name": "Gemini 3.1 Flash TTS Preview"},
]

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    import io
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()

def call_gemini_tts(api_key: str, model: str, voice: str, text: str, output_path: str) -> None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice
                    }
                }
            }
        }
    }
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()

    audio_b64 = None
    mime_type = ""
    for cand in data.get("candidates", []):
        content = cand.get("content", {})
        for part in content.get("parts", []):
            inline_data = part.get("inlineData", {})
            if inline_data.get("mimeType", "").startswith("audio/"):
                audio_b64 = inline_data.get("data")
                mime_type = inline_data.get("mimeType")
                break
        if audio_b64:
            break

    if not audio_b64:
        raise ValueError("Gemini TTS did not return any audio data.")

    audio_bytes = base64.b64decode(audio_b64)
    if mime_type == "audio/L16" or (not audio_bytes.startswith(b"RIFF") and output_path.endswith(".wav")):
        audio_bytes = pcm_to_wav(audio_bytes, sample_rate=24000)

    with open(output_path, "wb") as f:
        f.write(audio_bytes)

def parse_api_keys(raw_keys: str) -> list[str]:
    keys = []
    for line in raw_keys.replace(",", "\n").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            keys.append(line)
    return keys

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = BASE_DIR / "templates" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    with open(index_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/api/voices")
async def get_voices():
    return {
        "edge": VOICE_GROUPS,
        "gemini": GEMINI_VOICES,
        "models": GEMINI_MODELS
    }

@app.post("/api/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    rate: str = Form("1.0"),
    tts_engine: str = Form("edge"),
    voice: str = Form(""),
    gemini_tts_voice: str = Form(""),
    gemini_tts_model: str = Form("gemini-3.1-flash-tts"),
    gemini_api_key: str = Form("")
):
    text_clean = text.strip()
    if not text_clean:
        raise HTTPException(status_code=400, detail="請輸入要合成的文字")

    file_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + str(uuid.uuid4())[:6]
    audio_filename = f"{file_id}.wav" if tts_engine == "gemini" else f"{file_id}.mp3"
    audio_path = OUTPUTS_DIR / audio_filename
    json_path = OUTPUTS_DIR / f"{file_id}.json"

    rate_str = "+0%"
    try:
        rate_val = float(rate)
        rate_pct = int(round((rate_val - 1.0) * 100))
        rate_str = f"{'+' if rate_pct >= 0 else ''}{rate_pct}%"
    except Exception:
        pass

    if tts_engine == "gemini":
        if not gemini_tts_voice:
            raise HTTPException(status_code=400, detail="請選擇 Gemini TTS 發音人")
        api_keys = parse_api_keys(gemini_api_key)
        if not api_keys:
            raise HTTPException(status_code=400, detail="請貼上 Gemini API 金鑰")

        success = False
        error_msg = ""
        key_index = 0

        candidate_models = [gemini_tts_model]
        for fallback in ["gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts", "gemini-3.1-flash-tts-preview"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        while not success and key_index < len(api_keys):
            current_key = api_keys[key_index]
            for model_to_try in candidate_models:
                try:
                    logger.info(f"Attempting Gemini TTS using key index {key_index} with model {model_to_try}")
                    call_gemini_tts(current_key, model_to_try, gemini_tts_voice, text_clean, str(audio_path))
                    success = True
                    break
                except Exception as ex:
                    error_msg = str(ex)
                    logger.warning(f"Failed Gemini TTS: model={model_to_try}, error={ex}")
                    continue
            if not success:
                key_index += 1

        if not success:
            raise HTTPException(status_code=500, detail=f"Gemini 語音生成失敗: {error_msg}")
    else:
        if not voice:
            raise HTTPException(status_code=400, detail="請選擇 Edge TTS 發音人")
        try:
            communicate = edge_tts.Communicate(text_clean, voice, rate=rate_str)
            await communicate.save(str(audio_path))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Edge TTS 語音生成失敗: {str(e)}")

    metadata = {
        "id": file_id,
        "text": text_clean,
        "engine": tts_engine,
        "voice": gemini_tts_voice if tts_engine == "gemini" else voice,
        "rate": rate,
        "filename": audio_filename,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "url": f"/api/download/{audio_filename}",
        "metadata": metadata
    }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="音訊檔案不存在")
    return FileResponse(file_path, media_type="audio/mpeg" if filename.endswith(".mp3") else "audio/wav")

@app.get("/api/history")
async def get_history():
    history_list = []
    json_files = glob.glob(str(OUTPUTS_DIR / "*.json"))
    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                audio_path = OUTPUTS_DIR / data["filename"]
                if audio_path.exists():
                    history_list.append(data)
                else:
                    os.remove(jf)
        except Exception:
            pass
    history_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return history_list

@app.delete("/api/history/{file_id}")
async def delete_history_item(file_id: str):
    json_path = OUTPUTS_DIR / f"{file_id}.json"
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                audio_path = OUTPUTS_DIR / data["filename"]
                if audio_path.exists():
                    os.remove(audio_path)
            os.remove(json_path)
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="記錄不存在")

if __name__ == "__main__":
    import uvicorn
    DEFAULT_PORT = 8004
    port = find_available_port(DEFAULT_PORT)
    local_ip = get_local_ip()

    banner_title = f"Pure TTS Generator (Port {port})" if port == DEFAULT_PORT else f"[!] 預設 Port {DEFAULT_PORT} 已被佔用，已自動切換至可用 Port {port}"
    print()
    print("=" * 55)
    print(f"    {banner_title}")
    print()
    print("    本機開啟網址:")
    print(f"    http://localhost:{port}")
    print()
    print("    同網域 / 旁人使用網址:")
    print(f"    http://{local_ip}:{port}")
    print("=" * 55)
    print()

    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
