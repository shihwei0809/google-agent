"""
PDF 語音旁白影片生成器
流程：上傳 PDF → 讀取腳本 → 人工檢視修正 → 選擇語音 → 生成影片
"""
import asyncio
import base64
import json
import logging
import os
import struct
import uuid
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# 載入 .env 設定檔（若存在）——換台電腦只需修改 .env，不需動程式碼
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)
except ImportError:
    pass  # python-dotenv 未安裝時，以系統環境變數為準

import edge_tts
import fitz  # PyMuPDF
import numpy as np
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

# ─── Config ───────────────────────────────────────────────────────────────────
FFMPEG_PATH = os.environ.get(
    "FFMPEG_PATH",
    "",  # 未設定時留空，依賴系統 PATH 中的 ffmpeg
)
if Path(FFMPEG_PATH).exists():
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

JOBS_DIR = Path("jobs")
JOBS_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Add file handler for diagnostics
file_handler = logging.FileHandler("server.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)

executor = ThreadPoolExecutor(max_workers=2)

# ─── GPU 硬體加速編碼偵測 ──────────────────────────────────────────────────────
import subprocess as _sp

def _detect_video_codec() -> str:
    """偵測系統可用的最快 H.264 編碼器：NVENC → AMF → QSV → libx264"""
    for codec in ("h264_nvenc", "h264_amf", "h264_qsv"):
        try:
            result = _sp.run(
                ["ffmpeg", "-f", "lavfi", "-i", "color=black:size=64x64:duration=0.1",
                 "-c:v", codec, "-f", "null", "-"],
                capture_output=True, timeout=8
            )
            # QSV 成功時 returncode=0；NVENC/AMF 無驅動時有特定錯誤字串
            stderr = result.stderr.decode(errors="ignore")
            if result.returncode == 0 or (
                codec == "h264_qsv" and "Error" not in stderr and "failed" not in stderr.lower()
            ):
                logger.info("GPU encoder detected: %s", codec)
                return codec
        except Exception:
            pass
    logger.info("No GPU encoder available, using libx264")
    return "libx264"

VIDEO_CODEC = _detect_video_codec()


# ─── Voice Groups ─────────────────────────────────────────────────────────────
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

ALL_VOICE_IDS = {v["id"] for grp in VOICE_GROUPS.values() for v in grp}

# ─── Gemini TTS Voices ────────────────────────────────────────────────────────
GEMINI_TTS_VOICES = [
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
GEMINI_TTS_MODELS = [
    {"id": "gemini-2.5-flash-preview-tts", "label": "Gemini 2.5 Flash TTS (推薦)"},
    {"id": "gemini-2.5-pro-preview-tts",   "label": "Gemini 2.5 Pro TTS (高品質)"},
    {"id": "gemini-3.1-flash-tts-preview", "label": "Gemini 3.1 Flash TTS (最新)"},
]
ALL_GEMINI_VOICE_IDS = {v["id"] for v in GEMINI_TTS_VOICES}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_api_keys(raw_keys: str) -> list[str]:
    """Parse newline or comma separated API keys into a list of clean strings."""
    if not raw_keys:
        return []
    keys = []
    for line in raw_keys.replace(",", "\n").splitlines():
        k = line.strip()
        if k:
            keys.append(k)
    return keys


def make_frame_1920x1080(img_path: str) -> str:
    """Letterbox a PDF page onto a 1920×1080 dark-navy canvas, save as PNG, return path."""
    out_path = img_path.replace(".png", "_framed.png")
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    scale = min(1920 / w, 1080 / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (1920, 1080), (12, 18, 36))
    canvas.paste(img, ((1920 - nw) // 2, (1080 - nh) // 2))
    canvas.save(out_path)
    return out_path

# ─── App ─────────────────────────────────────────────────────────────────────
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="PDF 語音旁白影片生成器")
templates = Jinja2Templates(directory="templates")
app.mount("/jobs", StaticFiles(directory="jobs"), name="jobs")

# In-memory job tracker
jobs: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    response = templates.TemplateResponse(request=request, name="index.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/api/voices")
async def get_voices():
    return VOICE_GROUPS


@app.get("/api/gemini-tts-voices")
async def get_gemini_tts_voices():
    return {"voices": GEMINI_TTS_VOICES, "models": GEMINI_TTS_MODELS}


@app.post("/api/preview")
async def preview_voice(
    engine: str = Form("edge"),
    voice: str = Form(...),
    model: str = Form("gemini-2.5-flash-preview-tts"),
    api_key: str = Form(""),
    rate: str = Form("-10%"),
):
    try:
        preview_id = str(uuid.uuid4())
        audio_ext = "wav" if engine == "gemini" else "mp3"
        out_path = JOBS_DIR / f"preview_{preview_id}.{audio_ext}"
        
        if engine == "gemini":
            api_keys = parse_api_keys(api_key)
            if not api_keys:
                raise HTTPException(status_code=400, detail="Gemini 語音試聽需要 API 金鑰。")
            
            success = False
            last_err = None
            key_index = 0
            candidate_models = [model]
            for fallback in ["gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts", "gemini-3.1-flash-tts-preview"]:
                if fallback not in candidate_models:
                    candidate_models.append(fallback)
            while not success and key_index < len(api_keys):
                current_key = api_keys[key_index]
                for model_to_try in candidate_models:
                    try:
                        text = f"Hello! This is a preview of the Gemini voice {voice}."
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            executor,
                            lambda: call_gemini_tts(current_key, model_to_try, voice, text, str(out_path))
                        )
                        success = True
                        break
                    except Exception as e:
                        logger.warning(f"Preview: key index {key_index} with model {model_to_try} failed: {e}.")
                        last_err = e
                if not success:
                    key_index += 1
                    
            if not success:
                raise last_err if last_err else ValueError("所有試聽 API 金鑰皆無效或已達限制。")
        else:
            text = "這是一段 Edge 語音的試聽片段。"
            if voice.startswith("en-"):
                text = "Hello! This is a preview of the English voice."
            elif voice.startswith("ja-"):
                text = "こんにちは、音声プレビューです。"
            elif voice.startswith("ko-"):
                text = "안녕하세요, 음성 미리보기입니다."
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(str(out_path))
            
        return {"url": f"/jobs/preview_{preview_id}.{audio_ext}"}
    except Exception as e:
        logger.exception("Preview failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-page-audio")
async def generate_page_audio(
    job_id: str = Form(...),
    page_index: int = Form(...),
    text: str = Form(...),
    tts_engine: str = Form("edge"),
    voice: str = Form(...),
    rate: str = Form("-10%"),
    auto_pause: str = Form("true"),
    gemini_tts_voice: str = Form(""),
    gemini_tts_model: str = Form("gemini-2.5-flash-preview-tts"),
    gemini_api_key: str = Form(""),
):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="工作不存在，請重新上傳 PDF。")

    is_auto_pause = auto_pause.lower() == "true"
    audio_ext = "wav" if tts_engine == "gemini" else "mp3"
    audio_path = job_dir / f"audio_{page_index:03d}.{audio_ext}"

    

    # TTS – use placeholder if page is blank
    tts_text = text.strip() if text.strip() else "本頁無文字內容。"

    # Inject natural breaks at line breaks if auto_pause is enabled
    if is_auto_pause and text.strip():
        lines = tts_text.splitlines()
        processed_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line[-1] not in (
                "。", "，", "、", "！", "？", "；", "：",
                ".", ",", "!", "?", ";", ":", '"', "'", "」", "』"
            ):
                line += "。"
            processed_lines.append(line)
        tts_text = " ".join(processed_lines)

    try:
        if tts_engine == "gemini":
            api_keys = parse_api_keys(gemini_api_key)
            if not api_keys:
                raise HTTPException(status_code=400, detail="使用 Gemini TTS 需要提供 API 金鑰。")
            success = False
            last_err = None
            key_index = 0
            candidate_models = [gemini_tts_model]
            for fallback in ["gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts", "gemini-3.1-flash-tts-preview"]:
                if fallback not in candidate_models:
                    candidate_models.append(fallback)
            while not success and key_index < len(api_keys):
                current_key = api_keys[key_index]
                for model_to_try in candidate_models:
                    try:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            executor,
                            lambda: call_gemini_tts(current_key, model_to_try, gemini_tts_voice, tts_text, str(audio_path))
                        )
                        success = True
                        break
                    except Exception as e:
                        logger.warning(f"Single page TTS: key index {key_index} with model {model_to_try} failed: {e}.")
                        last_err = e
                if not success:
                    key_index += 1
            if not success:
                raise last_err if last_err else ValueError("所有提供的 Gemini API 金鑰皆已達到使用上限！")
        else:
            communicate = edge_tts.Communicate(tts_text, voice, rate=rate)
            await communicate.save(str(audio_path))

        # 防衝突：刪除另一種副檔名的音檔
        other_ext = "mp3" if audio_ext == "wav" else "wav"
        other_path = job_dir / f"audio_{page_index:03d}.{other_ext}"
        if other_path.exists():
            try:
                other_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete conflicting audio file {other_path}: {e}")

        # 更新 script_backup.json 中的文字
        backup_path = job_dir / "script_backup.json"
        if backup_path.exists():
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                
                pages = backup_data.get("pages", [])
                while len(pages) <= page_index:
                    pages.append("")
                pages[page_index] = text
                backup_data["pages"] = pages
                
                backup_data["voice"] = voice
                backup_data["tts_engine"] = tts_engine
                if tts_engine == "gemini":
                    backup_data["gemini_tts_voice"] = gemini_tts_voice
                    backup_data["gemini_tts_model"] = gemini_tts_model
                
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Updated script_backup.json for page {page_index}")
            except Exception as e:
                logger.warning(f"Failed to update script_backup.json: {e}")
        else:
            try:
                img_files = sorted(list(job_dir.glob("page_*.png")))
                orig_imgs = [f for f in img_files if not f.name.endswith("_framed.png")]
                total_pages = len(orig_imgs)
                
                pages = [""] * total_pages
                if page_index < total_pages:
                    pages[page_index] = text
                
                backup_data = {
                    "voice": voice,
                    "tts_engine": tts_engine,
                    "total_pages": total_pages,
                    "pages": pages
                }
                if tts_engine == "gemini":
                    backup_data["gemini_tts_voice"] = gemini_tts_voice
                    backup_data["gemini_tts_model"] = gemini_tts_model

                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Created script_backup.json and saved page {page_index}")
            except Exception as e:
                logger.warning(f"Failed to initialize script_backup.json: {e}")

        import time
        audio_url = f"/jobs/{job_id}/audio_{page_index:03d}.{audio_ext}?t={int(time.time() * 1000)}"
        return {"status": "success", "url": audio_url}

    except Exception as e:
        logger.exception("Single page generate failed")
        raise HTTPException(status_code=500, detail=str(e))


import base64
import requests

_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        logger.info("Initializing EasyOCR reader...")
        _easyocr_reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
    return _easyocr_reader

def call_gemini_api(api_key: str, model: str, image_path: Path) -> str:
    """Call Google Gemini API with a local image to generate presentation narration."""
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        prompt = (
            "你是一個專業的簡報導覽配音員。請根據這張簡報投影片的畫面內容，編寫一段適合語音朗讀、語氣自然流暢、"
            "發音清晰的繁體中文簡報旁白腳本（字數約 120-250 字）。請注意：\n"
            "1. 只回傳旁白文字內容，不要包含頁碼、簡報標題等無關標記。\n"
            "2. 不要包含任何額外說明文字或引號，直接輸出旁白內容即可。"
        )
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": img_b64
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise e

def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Wrap raw PCM bytes into a proper WAV container."""
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
    """Call Gemini TTS API, save audio as WAV file."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
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
        raise ValueError(f"Gemini TTS failed, no audio returned. Response keys: {list(data.keys())}")

    audio_bytes = base64.b64decode(audio_b64)
    if mime_type == "audio/L16" or (not audio_bytes.startswith(b"RIFF") and output_path.endswith(".wav")):
        audio_bytes = pcm_to_wav(audio_bytes, sample_rate=24000)

    with open(output_path, "wb") as f:
        f.write(audio_bytes)


def generate_lyria_bgm(api_key: str, prompt: str, output_path: str) -> None:
    """Call Gemini Lyria API to generate background music clip, save as MP3."""
    # 強制純器樂：不要人聲、不要演唱
    instrumental_suffix = ", instrumental only, no vocals, no singing, no lyrics, pure background music"
    if "instrumental" not in prompt.lower():
        prompt = prompt.rstrip(", ") + instrumental_suffix
    url = f"https://generativelanguage.googleapis.com/v1beta/models/lyria-3-clip-preview:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    logger.info("Calling Gemini Lyria API with prompt: %s", prompt)
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()

    audio_b64 = None
    for cand in data.get("candidates", []):
        content = cand.get("content", {})
        for part in content.get("parts", []):
            inline_data = part.get("inlineData", {})
            if inline_data.get("mimeType", "").startswith("audio/"):
                audio_b64 = inline_data.get("data")
                break
        if audio_b64:
            break

    if not audio_b64:
        raise ValueError(f"Gemini Lyria failed, no audio returned. Response keys: {list(data.keys())}")

    audio_bytes = base64.b64decode(audio_b64)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)


def call_grok_api(api_key: str, model: str, image_path: Path) -> str:
    """Call xAI Grok API with a local image to generate presentation narration."""
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        url = "https://api.xai.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        prompt = (
            "你是一個專業的簡報導覽配音員。請根據這張簡報投影片的畫面內容，編寫一段適合語音朗讀、語氣自然流暢、"
            "發音清晰的繁體中文簡報旁白腳本（字數約 120-250 字）。請注意：\n"
            "1. 只回傳旁白文字內容，不要包含頁碼、簡報標題等無關標記。\n"
            "2. 不要包含任何額外說明文字或引號，直接輸出旁白內容即可。"
        )
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}"
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return text.strip()
    except Exception as e:
        logger.error(f"Grok API call failed: {e}")
        raise e

@app.post("/api/extract")
def extract_pdf(
    file: UploadFile = File(...),
    method: str = Form("digital"),
    api_key: str = Form(""),
    model: str = Form(""),
):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="請上傳 PDF 格式的檔案。")

        import re
        import datetime
        pdf_name = Path(file.filename).stem
        # Allow alphanumeric, Chinese characters, dashes, and underscores
        safe_name = re.sub(r'[^\w\u4e00-\u9fa5\-]', '_', pdf_name)
        safe_name = re.sub(r'_{2,}', '_', safe_name).strip('_')
        if not safe_name:
            safe_name = "pdf_project"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = f"{safe_name}_{timestamp}"
        
        job_dir = JOBS_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            contents = file.file.read()
            doc = fitz.open(stream=contents, filetype="pdf")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF 讀取失敗：{e}")

        if len(doc) == 0:
            raise HTTPException(status_code=400, detail="PDF 檔案是空的。")

        pages_data = []
        api_keys = parse_api_keys(api_key)
        key_index = 0

        for i, page in enumerate(doc):
            # 1. 輸出高解析度 PNG（API 與 OCR 需要底圖）
            mat_hi = fitz.Matrix(2, 2)
            pix_hi = page.get_pixmap(matrix=mat_hi)
            img_path = job_dir / f"page_{i:03d}.png"
            pix_hi.save(str(img_path))

            # 2. 輸出縮圖供瀏覽器預覽與 AI 辨識 (改為清晰的 0.75 縮圖，體積大幅縮小解決上傳逾時)
            mat_th = fitz.Matrix(0.75, 0.75)
            pix_th = page.get_pixmap(matrix=mat_th)
            thumb_path = job_dir / f"thumb_{i:03d}.png"
            pix_th.save(str(thumb_path))

            # 3. 根據所選模式提取或生成腳本
            text = ""
            if method == "gemini" and api_keys:
                success = False
                while not success and key_index < len(api_keys):
                    current_key = api_keys[key_index]
                    try:
                        logger.info("Calling Gemini API for page %d (key index %d)...", i + 1, key_index)
                        text = call_gemini_api(current_key, model, thumb_path)
                        success = True
                    except Exception as e:
                        if "429" in str(e) or "limit" in str(e).lower() or "quota" in str(e).lower():
                            logger.warning("Key index %d rate limited. Switching to next key...", key_index)
                            key_index += 1
                        else:
                            logger.warning("Key index %d failed: %s. Trying next key...", key_index, e)
                            key_index += 1
                if not success:
                    logger.warning("All Gemini keys exhausted. Falling back to digital text.")
                    text = page.get_text().strip()
            elif method == "grok" and api_key:
                try:
                    logger.info("Calling Grok API for page %d...", i + 1)
                    text = call_grok_api(api_key, model, thumb_path)
                except Exception as e:
                    logger.warning("Grok extraction failed, falling back to digital text: %s", e)
                    text = page.get_text().strip()
            elif method == "easyocr":
                try:
                    logger.info("Running EasyOCR for page %d...", i + 1)
                    reader = get_easyocr_reader()
                    ocr_results = reader.readtext(str(img_path), detail=0, paragraph=True)
                    text = "\n".join(ocr_results).strip()
                except Exception as e:
                    logger.warning("EasyOCR failed, falling back to digital text: %s", e)
                    text = page.get_text().strip()
            else:
                # 預設：本機數位文字擷取
                text = page.get_text().strip()

            pages_data.append({
                "page_num": i + 1,
                "text": text,
                "thumbnail": f"/jobs/{job_id}/thumb_{i:03d}.png",
            })

        jobs[job_id] = {"status": "extracted", "total_pages": len(pages_data)}
        logger.info("Extracted %d pages, method=%s, job=%s", len(pages_data), method, job_id)
        return {"job_id": job_id, "pages": pages_data}
    except Exception as e:
        logger.exception("Error extracting PDF")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"系統內部錯誤：{e}")



@app.get("/api/get-page-audio")
async def get_page_audio(job_id: str, page_index: int, tts_engine: str = "edge"):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="工作不存在。")
    
    audio_ext = "wav" if tts_engine in ("gemini", "cloning") else "mp3"
    audio_path = job_dir / f"audio_{page_index:03d}.{audio_ext}"
    if not audio_path.exists():
        # check alternative extension
        alt_ext = "mp3" if audio_ext == "wav" else "wav"
        alt_path = job_dir / f"audio_{page_index:03d}.{alt_ext}"
        if alt_path.exists():
            audio_path = alt_path
            audio_ext = alt_ext
            
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="語音尚未生成，請先點擊「生成此頁語音」。")
        
    import time
    audio_url = f"/jobs/{job_id}/audio_{page_index:03d}.{audio_ext}?t={int(time.time() * 1000)}"
    return {"status": "success", "url": audio_url}

@app.post("/api/generate")
async def generate_video(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    scripts: str = Form(...),
    voice: str = Form(...),
    rate: str = Form("-10%"),
    auto_pause: str = Form("true"),
    tts_engine: str = Form("edge"),
    gemini_tts_voice: str = Form(""),
    gemini_tts_model: str = Form("gemini-2.5-flash-preview-tts"),
    gemini_api_key: str = Form(""),
    none_duration: float = Form(3.0),
    enable_bgm: str = Form("false"),
    bgm_type: str = Form("local"),
    ai_bgm_prompt: str = Form(""),
    bgm_volume: float = Form(0.1),
    watermark_text: str = Form(""),
):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="工作不存在，請重新上傳 PDF。")

    try:
        scripts_list: list[str] = json.loads(scripts)
    except Exception:
        raise HTTPException(status_code=400, detail="腳本格式錯誤。")

    if tts_engine == "gemini":
        if gemini_tts_voice not in ALL_GEMINI_VOICE_IDS:
            raise HTTPException(status_code=400, detail=f"不支援的 Gemini TTS 語音：{gemini_tts_voice}")
        if not gemini_api_key:
            raise HTTPException(status_code=400, detail="使用 Gemini TTS 需要提供 API 金鑰。")
    elif tts_engine == "none":
        # 無語音模式，略過語音驗證
        pass
    else:
        if voice not in ALL_VOICE_IDS:
            raise HTTPException(status_code=400, detail=f"不支援的聲音：{voice}")

    is_auto_pause = auto_pause.lower() == "true"
    is_enable_bgm = enable_bgm.lower() == "true"

    # ── 自動備份腳本 ──────────────────────────────────────────────────────────
    # 合成前將腳本存到 job 資料夾，讓使用者日後可下載並重新合成，不需重新讀取 PDF
    import datetime
    backup_path = job_dir / "script_backup.json"
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump({
                "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "voice": voice,
                "tts_engine": tts_engine,
                "total_pages": len(scripts_list),
                "pages": scripts_list,
                "none_duration": none_duration,
                "enable_bgm": is_enable_bgm,
                "bgm_type": bgm_type,
                "ai_bgm_prompt": ai_bgm_prompt,
                "bgm_volume": bgm_volume,
                "watermark_text": watermark_text,
            }, f, ensure_ascii=False, indent=2)
        logger.info("Script backup saved to %s", backup_path)
    except Exception as e:
        logger.warning("Failed to save script backup: %s", e)

    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "total": len(scripts_list),
        "step": "準備中…",
    }
    background_tasks.add_task(
        _run_generation, job_id, scripts_list, voice, rate, is_auto_pause, job_dir,
        tts_engine, gemini_tts_voice, gemini_tts_model, gemini_api_key, none_duration, is_enable_bgm,
        bgm_type, ai_bgm_prompt, bgm_volume, watermark_text
    )
    return {"job_id": job_id, "status": "processing"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id in jobs:
        return jobs[job_id]
    # 如果 server 重啟導致 in-memory jobs 清空，從磁碟判斷狀態
    job_dir = JOBS_DIR / job_id
    if job_dir.exists():
        if (job_dir / "output.mp4").exists():
            return {"status": "done", "progress": 0, "total": 0, "step": "已完成"}
        error_file = job_dir / "error.txt"
        if error_file.exists():
            return {"status": "error", "error": error_file.read_text(encoding="utf-8")}
        # job 目錄存在但尚未完成（可能正在生成中）
        return {"status": "processing", "progress": 0, "total": 0, "step": "正在導入影片..."}
    raise HTTPException(status_code=404, detail="工作不存在，請重新上傳 PDF。")


@app.post("/api/rescue/video-to-script")
async def rescue_video_to_script(
    file: UploadFile = File(...),
    gemini_api_key: str = Form(...),
    gemini_model: str = Form("gemini-1.5-flash"),
):
    """上傳已生成的 MP4 影片，提取音訊並呼叫 Gemini API 聽寫還原為腳本文字 (.txt)。"""
    if not file.filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="請上傳 MP4 格式的影片檔案。")

    if not gemini_api_key.strip():
        raise HTTPException(status_code=400, detail="請提供 Gemini API 金鑰以進行語音聽寫還原。")

    import tempfile
    import requests
    from moviepy import VideoFileClip

    temp_dir = Path(tempfile.gettempdir())
    temp_mp4 = temp_dir / f"rescue_{uuid.uuid4().hex}.mp4"
    temp_mp3 = temp_mp4.with_suffix(".mp3")

    try:
        # 1. 保存臨時影片檔
        with open(temp_mp4, "wb") as f:
            f.write(await file.read())

        # 2. 提取音訊音軌為 MP3
        logger.info("Extracting audio from uploaded video: %s", file.filename)
        try:
            video = VideoFileClip(str(temp_mp4))
            if video.audio is None:
                raise ValueError("影片中不包含任何音軌。")
            video.audio.write_audiofile(str(temp_mp3), logger=None)
            video.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"影片音軌提取失敗：{e}")

        # 3. 呼叫 Gemini 進行語音識別與腳本切分
        logger.info("Uploading audio to Gemini for speech-to-text transcription...")
        api_keys = parse_api_keys(gemini_api_key)
        if not api_keys:
            raise HTTPException(status_code=400, detail="無效的 API 金鑰。")
        
        # 讀取音訊內容
        with open(temp_mp3, "rb") as f:
            audio_bytes = f.read()

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        prompt = (
            "你是一個專業的語音聽寫助理。這是一個簡報旁白影片的音訊檔案，請仔細聆聽，"
            "將其中的語音內容逐字聽寫出來（使用繁體中文）。並且非常重要：\n"
            "請根據語音中的明顯停頓、投影片切換感，將內容切分成每頁的旁白腳本，"
            "並完全使用以下格式輸出：\n\n"
            "=== 第 1 頁 ===\n"
            "(該頁旁白文字)\n\n"
            "=== 第 2 頁 ===\n"
            "(該頁旁白文字)\n\n"
            "不要輸出任何非格式內的引言、說明或額外字元。直接輸出格式化的腳本即可。"
        )
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "audio/mp3",
                            "data": audio_b64
                        }
                    }
                ]
            }]
        }
        
        # 建立候選模型清單，使用者選取的排第一
        candidate_models = [gemini_model]
        all_models = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-3.5-flash",
            "gemini-3.5-pro",
            "gemini-2.5-flash",
            "gemini-1.5-pro-latest"
        ]
        for m in all_models:
            if m not in candidate_models:
                candidate_models.append(m)

        txt_content = ""
        last_error = ""

        # 遍歷候選模型，直到成功為止
        for model_name in candidate_models:
            logger.info("Trying voice transcription with Gemini model: %s", model_name)
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_keys[0]}"
            try:
                headers = {"Content-Type": "application/json; charset=utf-8"}
                response = requests.post(
                    gemini_url,
                    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                    headers=headers,
                    timeout=120
                )
                if response.status_code != 200:
                    last_error = f"{model_name} failed (HTTP {response.status_code}): {response.text}"
                    logger.warning(last_error)
                    continue
                
                data = response.json()
                txt_content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if txt_content:
                    logger.info("Successfully transcribed with model: %s", model_name)
                    break
            except Exception as e:
                last_error = f"{model_name} failed: {e}"
                logger.warning(last_error)
                continue

        if not txt_content:
            raise ValueError(f"所有嘗試的模型皆辨識失敗。最後的錯誤訊息：{last_error}")

        # 4. 回傳 TXT 下載
        from fastapi.responses import Response
        from urllib.parse import quote
        safe_filename = quote(Path(file.filename).stem + "_還原腳本.txt")
        return Response(
            content=txt_content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{safe_filename}"},
        )

    except Exception as e:
        logger.exception("Error extracting script from video")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"影片腳本還原失敗：{e}")
    finally:
        # 清除臨時檔案
        if temp_mp4.exists():
            try: temp_mp4.unlink()
            except: pass
        if temp_mp3.exists():
            try: temp_mp3.unlink()
            except: pass


@app.get("/api/script/{job_id}")
async def download_script(job_id: str):
    """下載指定工作的腳本備份（.txt 格式），可用於日後重新合成。"""
    backup_path = JOBS_DIR / job_id / "script_backup.json"
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="找不到腳本備份，請重新合成一次以產生備份。")
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pages: list[str] = data.get("pages", [])
        lines = []
        for i, text in enumerate(pages):
            lines.append(f"=== 第 {i + 1} 頁 ===")
            lines.append(text)
            lines.append("")
        txt_content = "\n".join(lines)
        from fastapi.responses import Response
        return Response(
            content=txt_content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="script_{job_id[:8]}.txt"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取備份失敗：{e}")


@app.get("/api/download/{job_id}")
async def download_video(job_id: str):
    video_path = JOBS_DIR / job_id / "output.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="影片尚未生成完成。")
    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename="narration_video.mp4",
        headers={"Content-Disposition": 'attachment; filename="narration_video.mp4"'},
    )


async def _run_generation(
    job_id: str,
    scripts: list[str],
    voice: str,
    rate: str,
    auto_pause: bool,
    job_dir: Path,
    tts_engine: str = "edge",
    gemini_tts_voice: str = "",
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts",
    gemini_api_key: str = "",
    none_duration: float = 3.0,
    enable_bgm: bool = False,
    bgm_type: str = "local",
    ai_bgm_prompt: str = "",
    bgm_volume: float = 0.1,
    watermark_text: str = "",
):
    """Background task: TTS synthesis + video assembly."""
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

        total = len(scripts)
        clips = []
        api_keys = parse_api_keys(gemini_api_key)
        key_index = 0

        # ── 讀取歷史腳本備份以供比對快取 ──────────────────────────────────────────
        backup_path = job_dir / "script_backup.json"
        cached_pages = []
        cached_voice = None
        cached_engine = None
        cached_gemini_voice = None
        cached_gemini_model = None
        cached_rate = None
        if backup_path.exists():
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                cached_pages = backup_data.get("pages", [])
                cached_voice = backup_data.get("voice")
                cached_engine = backup_data.get("tts_engine")
                cached_gemini_voice = backup_data.get("gemini_tts_voice", "")
                cached_gemini_model = backup_data.get("gemini_tts_model", "")
                cached_rate = backup_data.get("rate", rate) 
            except Exception as e:
                logger.warning(f"Failed to read backup script for cache comparison: {e}")

        for i, text in enumerate(scripts):
            jobs[job_id]["step"] = f"第 {i + 1}/{total} 頁：製作簡報畫面中…" if tts_engine == "none" else f"第 {i + 1}/{total} 頁：生成語音旁白…"
            img_path = str(job_dir / f"page_{i:03d}.png")
            
            # Ensure image exists (fallback to blank)
            if not Path(img_path).exists():
                logger.warning("Image not found for page %d, skipping", i)
                continue

            # Make 1920×1080 framed image
            framed_path = make_frame_1920x1080(img_path)

            if tts_engine == "none":
                # 無語音模式：每頁顯示時間直接設定為 none_duration
                clip = ImageClip(framed_path, duration=none_duration)
                clips.append(clip)
                jobs[job_id]["progress"] = i + 1
            else:
                # 有語音模式
                audio_ext = "wav" if tts_engine == "gemini" else "mp3"
                audio_path = str(job_dir / f"audio_{i:03d}.{audio_ext}")
                tts_text = text.strip() if text.strip() else "本頁無文字內容。"

                if auto_pause and text.strip():
                    lines = tts_text.splitlines()
                    processed_lines = []
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if line[-1] not in (
                            "。", "，", "、", "！", "？", "；", "：",
                            ".", ",", "!", "?", ";", ":", '"', "'", "」", "』"
                        ):
                            line += "。"
                        processed_lines.append(line)
                    tts_text = " ".join(processed_lines)

                # 比對文字與語音設定是否完全相同且音訊檔案存在
                can_reuse = False
                if (
                    cached_pages and
                    i < len(cached_pages) and
                    cached_pages[i] == text and
                    cached_voice == voice and
                    cached_engine == tts_engine and
                    cached_rate == rate and
                    (tts_engine != "gemini" or (cached_gemini_voice == gemini_tts_voice and cached_gemini_model == gemini_tts_model)) and
                    Path(audio_path).exists()
                ):
                    try:
                        import wave
                        if audio_path.endswith('.wav'):
                            with wave.open(audio_path, 'rb') as _:
                                pass
                        else:
                            import os
                            if os.path.getsize(audio_path) < 1000:
                                raise ValueError("MP3 file too small")
                        logger.info(f"Page {i + 1} script and voice settings unchanged. Reusing existing audio: {audio_path}")
                        can_reuse = True
                    except Exception as e:
                        logger.warning(f"Audio cache invalid for page {i+1}, will regenerate: {e}")
                        can_reuse = False

                if not can_reuse:
                    if tts_engine == "gemini":
                        success = False
                        candidate_models = [gemini_tts_model]
                        for fallback in ["gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts", "gemini-3.1-flash-tts-preview"]:
                            if fallback not in candidate_models:
                                candidate_models.append(fallback)
                        while not success and key_index < len(api_keys):
                            current_key = api_keys[key_index]
                            for model_to_try in candidate_models:
                                try:
                                    loop = asyncio.get_event_loop()
                                    await loop.run_in_executor(
                                        executor,
                                        lambda t=tts_text, p=audio_path, k=current_key, m=model_to_try: call_gemini_tts(
                                            k, m, gemini_tts_voice, t, p
                                        )
                                    )
                                    success = True
                                    break
                                except Exception as e:
                                    logger.warning("Gemini TTS: Key index %d with model %s failed: %s", key_index, model_to_try, e)
                            if not success:
                                key_index += 1
                        if not success:
                            raise ValueError("所有提供的 Gemini API 金鑰皆已達到使用上限！無法繼續生成語音。")
                    else:
                        communicate = edge_tts.Communicate(tts_text, voice, rate=rate)
                        await communicate.save(audio_path)

                    other_ext = "mp3" if audio_ext == "wav" else "wav"
                    other_path = job_dir / f"audio_{i:03d}.{other_ext}"
                    if other_path.exists():
                        try:
                            other_path.unlink()
                        except Exception as e:
                            logger.warning(f"Failed to delete conflicting audio file {other_path}: {e}")

                # Build clip with voice audio
                audio = AudioFileClip(audio_path)
                duration = max(audio.duration, 1.5)
                clip = ImageClip(framed_path, duration=duration).with_audio(audio)
                clips.append(clip)
                jobs[job_id]["progress"] = i + 1

        if not clips:
            raise ValueError("沒有任何可處理的頁面。")

        jobs[job_id]["step"] = "正在合成影片與載入音樂（可能需要數分鐘）…"

        output_path = str(job_dir / "output.mp4")
        loop = asyncio.get_event_loop()

        def write_video():
            final = concatenate_videoclips(clips, method="chain")
            
            # ── 混入背景音樂 (BGM) ──────────────────────────────────────────────────
            # 只有在純圖片 (tts_engine == "none")，或者有語音且選取 enable_bgm 為 True 時才載入
            if tts_engine == "none" or enable_bgm:
                bgm_path = None
                if bgm_type == "ai" and api_keys:
                    temp_ai_bgm = job_dir / "ai_bgm.mp3"
                    try:
                        generate_lyria_bgm(api_keys[0], ai_bgm_prompt, str(temp_ai_bgm))
                        if temp_ai_bgm.exists():
                            bgm_path = temp_ai_bgm
                    except Exception as e:
                        logger.warning(f"Failed to generate AI BGM via Lyria: {e}. Falling back to default BGM.")
                
                if not bgm_path:
                    bgm_dir = Path(__file__).parent / "assets"
                    bgm_dir.mkdir(exist_ok=True)
                    bgm_path = bgm_dir / "background_music.mp3"

                if bgm_path.exists():
                    try:
                        from moviepy import CompositeAudioClip
                        from moviepy.audio.fx import AudioLoop, AudioFadeOut
                        
                        bg_music = AudioFileClip(str(bgm_path))
                        # 循環播放或裁切音樂對齊影片總長度
                        if bg_music.duration < final.duration:
                            bg_music = bg_music.with_effects([AudioLoop(duration=final.duration)])
                        else:
                            bg_music = bg_music.subclipped(0, final.duration)
                        
                        # 背景音樂套用淡出
                        bg_music = bg_music.with_effects([AudioFadeOut(duration=2.0)])
                        
                        if tts_engine == "none" or final.audio is None:
                            # 無語音模式： BGM 為主音軌，但仍需套用音量設定
                            vol = bgm_volume if bgm_volume > 0 else 1.0
                            if vol != 1.0:
                                bg_music = bg_music.with_volume_scaled(vol)
                            final.audio = bg_music
                        else:
                            # 有語音模式：調降背景音樂音量後與人聲語音音軌重疊混音
                            voice_audio = final.audio
                            if voice_audio is not None:
                                bg_music = bg_music.with_volume_scaled(bgm_volume if bgm_volume > 0 else 0.1)
                                mixed_audio = CompositeAudioClip([voice_audio, bg_music])
                                final.audio = mixed_audio
                    except Exception as e:
                        logger.warning(f"Failed to mix background music: {e}. Video will be exported without BGM.")
                else:
                    logger.warning(f"Background music file not found at {bgm_path}. Skipping BGM mix.")
                    
                # ── BGM 出處浮水印 ──
                if enable_bgm and bgm_path and bgm_path.exists():
                    watermark_path = str(job_dir / "watermark.png")
                    bgm_label = watermark_text.strip()
                    if not bgm_label:
                        bgm_label = "🎵 BGM: " + ("AI Generated Music" if bgm_type == "ai" else "Background Music")
                    if create_bgm_watermark_png(watermark_path, bgm_label):
                        from moviepy import CompositeVideoClip
                        w_clip = ImageClip(watermark_path, duration=final.duration)
                        final = CompositeVideoClip([final, w_clip])

            _vf_kw = dict(fps=5, codec=VIDEO_CODEC, audio_codec="aac", threads=4, logger=None)
            if VIDEO_CODEC == "libx264":
                _vf_kw["preset"] = "ultrafast"
            final.write_videofile(output_path, **_vf_kw)
            final.close()
            for c in clips:
                c.close()

        await loop.run_in_executor(executor, write_video)

        jobs[job_id] = {
            "status": "done",
            "progress": total,
            "total": total,
            "step": "影片生成完成！",
        }
        logger.info("Job %s completed.", job_id)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        jobs[job_id] = {"status": "error", "error": str(exc), "step": "發生錯誤"}


@app.get("/api/jobs/list")
async def list_jobs():
    import datetime
    result = []
    if not JOBS_DIR.exists():
        return {"jobs": []}
    
    for d in JOBS_DIR.iterdir():
        if d.is_dir() and not d.name.startswith("preview_"):
            # Count pages (original or framed)
            pages = len(list(d.glob("page_*_framed.png")))
            if pages == 0:
                pages = len(list(d.glob("page_*.png")))
            
            # Count audios
            audios = len(list(d.glob("audio_*")))
            has_video = (d / "output.mp4").exists()
            
            try:
                # 尋找目錄下所有檔案的最晚修改時間，以反映專案的真實異動時間
                files = list(d.glob("*"))
                if files:
                    mtime = max(os.path.getmtime(str(f)) for f in files)
                else:
                    mtime = os.path.getmtime(str(d))
                time_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                time_str = "未知時間"
                
            if pages > 0:
                result.append({
                    "job_id": d.name,
                    "pages": pages,
                    "audios": audios,
                    "has_video": has_video,
                    "time": time_str
                })
    # Sort by time descending
    result.sort(key=lambda x: x["time"], reverse=True)
    return {"jobs": result}


@app.get("/api/jobs/load/{job_id}")
async def load_job_data(job_id: str):
    """讀取歷史專案的投影片與腳本資料，供編輯器直接載入。"""
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="該專案目錄不存在。")

    # 1. 取得圖片頁數 (page_*.png 數量，排除 _framed.png)
    img_files = sorted(list(job_dir.glob("page_*.png")))
    orig_imgs = [f for f in img_files if not f.name.endswith("_framed.png")]
    total_pages = len(orig_imgs)

    if total_pages == 0:
        raise HTTPException(status_code=400, detail="此專案內無投影片圖片，無法載入。")

    # 2. 嘗試讀取備份的腳本資料
    backup_path = job_dir / "script_backup.json"
    backup_pages = []
    voice = ""
    tts_engine = "edge"
    gemini_tts_voice = ""
    gemini_tts_model = "gemini-2.5-flash-preview-tts"
    rate = "-10%"
    auto_pause = "true"

    if backup_path.exists():
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                backup_pages = data.get("pages", [])
                voice = data.get("voice", "")
                tts_engine = data.get("tts_engine", "edge")
                gemini_tts_voice = data.get("gemini_tts_voice", "")
                gemini_tts_model = data.get("gemini_tts_model", "gemini-2.5-flash-preview-tts")
                rate = data.get("rate", "-10%")
                auto_pause = "true" if data.get("auto_pause", True) else "false"
        except Exception as e:
            logger.warning("Failed to load script backup for job %s: %s", job_id, e)

    # 3. 建立網頁所需的 pages_data
    pages_data = []
    for i in range(total_pages):
        # 讀取備份的文字，沒有的話就給空白
        text = ""
        if i < len(backup_pages):
            text = backup_pages[i]
        
        # 確保 thumbnail 存在，若沒有 thumb_xxx.png 就用 page_xxx.png 替代
        thumb_name = f"thumb_{i:03d}.png"
        if not (job_dir / thumb_name).exists():
            thumb_name = f"page_{i:03d}.png"

        pages_data.append({
            "page_num": i + 1,
            "text": text,
            "thumbnail": f"/jobs/{job_id}/{thumb_name}",
        })

    return {
        "job_id": job_id,
        "pages": pages_data,
        "voice": voice,
        "tts_engine": tts_engine,
        "gemini_tts_voice": gemini_tts_voice,
        "gemini_tts_model": gemini_tts_model,
        "rate": rate,
        "auto_pause": auto_pause,
    }


def create_bgm_watermark_png(output_png_path: str, text: str = "🎵 BGM: Background Music"):
    """Draw a translucent copyright / source watermark PNG using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Windows CJK 字型候選清單（支援繁體中文）
        font_candidates = [
            "C:/Windows/Fonts/msjh.ttc",       # Microsoft JhengHei (微軟正黑體)
            "C:/Windows/Fonts/msjhbd.ttc",
            "C:/Windows/Fonts/mingliu.ttc",    # MingLiU
            "C:/Windows/Fonts/kaiu.ttf",       # KaiU
            "C:/Windows/Fonts/msyh.ttc",       # Microsoft YaHei (Simplified)
            "C:/Windows/Fonts/arial.ttf",       # 英文 fallback
        ]
        font = None
        for fp in font_candidates:
            try:
                font = ImageFont.truetype(fp, 22)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = 1920 - tw - 40
        y = 1080 - th - 30
        
        pad = 8
        draw.rounded_rectangle([x - pad, y - pad, x + tw + pad, y + th + pad], radius=6, fill=(0, 0, 0, 140))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 220))
        img.save(output_png_path, "PNG")
        return True
    except Exception as e:
        logger.warning(f"Failed to create BGM watermark PNG: {e}")
        return False


@app.post("/api/jobs/rebuild/{job_id}")
async def rebuild_video(
    job_id: str,
    background_tasks: BackgroundTasks,
    scripts: str = Form("[]"),
    tts_engine: str = Form("edge"),
    none_duration: float = Form(3.0),
    silent_duration: float = Form(3.0),
    enable_bgm: str = Form("false"),
    use_bgm: str = Form("false"),
    bgm_type: str = Form("local"),
    ai_bgm_prompt: str = Form(""),
    bgm_volume: float = Form(0.1),
    bgm_file: UploadFile = File(None),
    watermark_text: str = Form(""),
):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="該專案目錄不存在。")
        
    final_none_duration = silent_duration if silent_duration != 3.0 else none_duration
    is_enable_bgm = enable_bgm.lower() == "true" or use_bgm.lower() == "true"

    # Save uploaded BGM if provided
    if bgm_file and bgm_file.filename:
        ext = os.path.splitext(bgm_file.filename)[1].lower() or ".mp3"
        bgm_path = job_dir / f"bgm{ext}"
        for old_bgm in job_dir.glob("bgm.*"):
            try: old_bgm.unlink()
            except: pass
        with open(bgm_path, "wb") as f:
            f.write(await bgm_file.read())
        logger.info("Saved uploaded background music to %s", bgm_path)

    # Save / update script backup with rebuild parameters
    backup_path = job_dir / "script_backup.json"
    existing_data = {}
    if backup_path.exists():
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    try:
        scripts_list = json.loads(scripts) if scripts and scripts != "[]" else existing_data.get("pages", [])
    except Exception:
        scripts_list = existing_data.get("pages", [])

    existing_data.update({
        "tts_engine": tts_engine,
        "none_duration": final_none_duration,
        "enable_bgm": is_enable_bgm,
        "bgm_type": bgm_type,
        "ai_bgm_prompt": ai_bgm_prompt,
        "bgm_volume": bgm_volume,
        "watermark_text": watermark_text,
    })
    if scripts_list:
        existing_data["pages"] = scripts_list
        existing_data["total_pages"] = len(scripts_list)
        
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update script_backup.json on rebuild: {e}")

    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "total": 0,
        "step": "排隊準備重新合成...",
    }
    background_tasks.add_task(
        _run_rebuild,
        job_id,
        tts_engine,
        final_none_duration,
        is_enable_bgm,
        bgm_type,
        ai_bgm_prompt,
        bgm_volume,
        watermark_text,
    )
    return {"job_id": job_id, "status": "processing"}


async def _run_rebuild(
    job_id: str,
    tts_engine: str = "edge",
    none_duration: float = 3.0,
    enable_bgm: bool = False,
    bgm_type: str = "local",
    ai_bgm_prompt: str = "",
    bgm_volume: float = 0.1,
    watermark_text: str = "",
):
    """Background task: rebuild video using existing images, audio files or silent duration."""
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip, CompositeAudioClip
        from moviepy.audio.fx import AudioLoop, AudioFadeOut
        
        job_dir = JOBS_DIR / job_id
        
        # Read backup script to recover missing defaults if necessary
        backup_path = job_dir / "script_backup.json"
        if backup_path.exists():
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                if tts_engine == "edge" and "tts_engine" in backup_data:
                    tts_engine = backup_data.get("tts_engine", tts_engine)
                if none_duration == 3.0 and "none_duration" in backup_data:
                    none_duration = backup_data.get("none_duration", none_duration)
                if not enable_bgm and "enable_bgm" in backup_data:
                    enable_bgm = backup_data.get("enable_bgm", enable_bgm)
                if bgm_type == "local" and "bgm_type" in backup_data:
                    bgm_type = backup_data.get("bgm_type", bgm_type)
            except Exception as e:
                logger.warning(f"Rebuild: failed to read backup data: {e}")

        # Determine number of pages
        img_files = sorted(list(job_dir.glob("page_*.png")))
        orig_imgs = [f for f in img_files if not f.name.endswith("_framed.png")]
        total = len(orig_imgs)
        
        jobs[job_id]["total"] = total
        jobs[job_id]["step"] = "讀取現有影音檔案..."
        
        clips = []
        for i in range(total):
            jobs[job_id]["step"] = f"第 {i + 1}/{total} 頁：製作影音畫面中…"
            img_path = job_dir / f"page_{i:03d}_framed.png"
            if not img_path.exists():
                img_path = job_dir / f"page_{i:03d}.png"
                
            if not img_path.exists():
                logger.warning(f"Rebuild: page_{i:03d} image not found.")
                continue
                
            framed_path = img_path
            if not img_path.name.endswith("_framed.png"):
                framed_path = Path(make_frame_1920x1080(str(img_path)))

            if tts_engine == "none":
                # 無語音 (靜音模式): 直接依據 none_duration 切換圖片
                clip = ImageClip(str(framed_path), duration=none_duration)
                clips.append(clip)
            else:
                # 語音模式: 嘗試載入對應配音檔 (.mp3 或 .wav)
                audio_path = job_dir / f"audio_{i:03d}.mp3"
                if not audio_path.exists():
                    audio_path = job_dir / f"audio_{i:03d}.wav"
                    
                if audio_path.exists():
                    audio = AudioFileClip(str(audio_path))
                    duration = max(audio.duration, 1.5)
                    clip = ImageClip(str(framed_path), duration=duration).with_audio(audio)
                else:
                    # 找不到音檔時回退為單頁秒數
                    clip = ImageClip(str(framed_path), duration=none_duration)
                clips.append(clip)
                
            jobs[job_id]["progress"] = i + 1
            
        if not clips:
            raise ValueError("找不到任何可配對的投影片圖片。")
            
        jobs[job_id]["step"] = "正在重新合成影片（可能需要數分鐘）..."
        output_path = str(job_dir / "output.mp4")
        
        loop = asyncio.get_event_loop()
        def write_video():
            final = concatenate_videoclips(clips, method="chain")
            
            # ── BGM 背景音樂處理 ──
            bgm_files = list(job_dir.glob("bgm.*"))
            bgm_path = bgm_files[0] if bgm_files else None
            if not bgm_path and enable_bgm:
                bgm_dir = Path(__file__).parent / "assets"
                if (bgm_dir / "background_music.mp3").exists():
                    bgm_path = bgm_dir / "background_music.mp3"

            if bgm_path and bgm_path.exists():
                try:
                    logger.info(f"Rebuild mixing BGM: {bgm_path}")
                    bg_music = AudioFileClip(str(bgm_path))
                    if bg_music.duration < final.duration:
                        bg_music = bg_music.with_effects([AudioLoop(duration=final.duration)])
                    else:
                        bg_music = bg_music.subclipped(0, final.duration)
                    bg_music = bg_music.with_effects([AudioFadeOut(duration=2.0)])
                    
                    if tts_engine == "none" or final.audio is None:
                        final = final.with_audio(bg_music)
                    else:
                        voice_audio = final.audio
                        bg_music = bg_music.with_volume_scaled(bgm_volume if bgm_volume > 0 else 0.15)
                        final = final.with_audio(CompositeAudioClip([voice_audio, bg_music]))
                except Exception as e:
                    logger.warning(f"Rebuild BGM mixing failed: {e}")

            # ── BGM 出處浮水印 ──
            if enable_bgm and bgm_path and bgm_path.exists():
                watermark_path = str(job_dir / "watermark.png")
                bgm_label = watermark_text.strip()
                if not bgm_label:
                    bgm_label = "🎵 BGM: " + ("AI Generated Music" if bgm_type == "ai" else "Background Music")
                if create_bgm_watermark_png(watermark_path, bgm_label):
                    w_clip = ImageClip(watermark_path, duration=final.duration)
                    final = CompositeVideoClip([final, w_clip])

            _vf_kw = dict(fps=5, codec=VIDEO_CODEC, audio_codec="aac", threads=4, logger=None)
            if VIDEO_CODEC == "libx264":
                _vf_kw["preset"] = "ultrafast"
            final.write_videofile(output_path, **_vf_kw)
            final.close()
            for c in clips:
                c.close()
                
        await loop.run_in_executor(executor, write_video)
        
        jobs[job_id] = {
            "status": "done",
            "progress": total,
            "total": total,
            "step": "影片重新合成完成！",
        }
        logger.info("Rebuild job %s completed.", job_id)
        
    except Exception as exc:
        logger.exception("Rebuild job %s failed", job_id)
        jobs[job_id] = {"status": "error", "error": str(exc), "step": "合成失敗"}


import socket

def get_local_ip():
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

if __name__ == "__main__":
    import uvicorn
    DEFAULT_PORT = 8002
    port = find_available_port(DEFAULT_PORT)
    local_ip = get_local_ip()

    banner_title = f"PDF Video Generator (Port {port})" if port == DEFAULT_PORT else f"[!] 預設 Port {DEFAULT_PORT} 已被佔用，已自動切換至可用 Port {port}"
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
