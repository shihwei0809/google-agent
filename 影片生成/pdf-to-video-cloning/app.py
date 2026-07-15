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

# ─── 克隆聲音路徑（從 .env 或系統環境變數讀取）────────────────────────────────
_CLONING_DIR = Path(
    os.environ.get("CLONING_DIR", str(Path(__file__).parent.parent.parent / "AI 克隆聲音"))
)

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
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/voices")
async def get_voices():
    return VOICE_GROUPS


@app.get("/api/gemini-tts-voices")
async def get_gemini_tts_voices():
    return {"voices": GEMINI_TTS_VOICES, "models": GEMINI_TTS_MODELS}


@app.get("/api/cloned-voices")
async def get_cloned_voices():
    """List all available cloned voices in the AI voice cloning project."""
    voices_dir = _CLONING_DIR / "voices"
    if not voices_dir.exists():
        return {"voices": []}
    voices = []
    for d in voices_dir.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            ref_path = d / "ref_voice.wav"
            if ref_path.exists():
                voices.append(d.name)
    return {"voices": sorted(voices)}


@app.post("/api/preview")
async def preview_voice(
    engine: str = Form("edge"),
    voice: str = Form(...),
    model: str = Form("gemini-2.5-flash-preview-tts"),
    api_key: str = Form(""),
):
    try:
        preview_id = str(uuid.uuid4())
        audio_ext = "wav" if engine in ("gemini", "cloning") else "mp3"
        out_path = JOBS_DIR / f"preview_{preview_id}.{audio_ext}"
        
        if engine == "gemini":
            api_keys = parse_api_keys(api_key)
            if not api_keys:
                raise HTTPException(status_code=400, detail="Gemini 語音試聽需要 API 金鑰。")
            
            success = False
            last_err = None
            key_index = 0
            while not success and key_index < len(api_keys):
                current_key = api_keys[key_index]
                try:
                    text = f"Hello! This is a preview of the Gemini voice {voice}."
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        executor,
                        lambda: call_gemini_tts(current_key, model, voice, text, str(out_path))
                    )
                    success = True
                except Exception as e:
                    logger.warning(f"Preview: key index {key_index} failed: {e}. Trying next key...")
                    last_err = e
                    key_index += 1
                    
            if not success:
                raise last_err if last_err else ValueError("所有試聽 API 金鑰皆無效或已達限制。")
        elif engine == "cloning":
            import subprocess
            python_exe = str(_CLONING_DIR / ".venv" / "Scripts" / "python.exe")
            clone_script = str(_CLONING_DIR / "clone.py")
            text = "這是一段本機克隆聲音的試聽片段。"
            
            cmd = [
                python_exe, clone_script,
                text,
                "--voice", voice,
                "--output", str(out_path.resolve())
            ]
            
            logger.info(f"Running cloning preview subprocess: {cmd}")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                lambda: subprocess.run(cmd, check=True, cwd=str(_CLONING_DIR))
            )
        else:
            text = "這是一段 Edge 語音的試聽片段。"
            if voice.startswith("en-"):
                text = "Hello! This is a preview of the English voice."
            elif voice.startswith("ja-"):
                text = "こんにちは、音声プレビューです。"
            elif voice.startswith("ko-"):
                text = "안녕하세요, 음성 미리보기입니다."
            communicate = edge_tts.Communicate(text, voice, rate="-10%")
            await communicate.save(str(out_path))
            
        return {"url": f"/jobs/preview_{preview_id}.{audio_ext}"}
    except Exception as e:
        logger.exception("Preview failed")
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
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def call_gemini_tts(api_key: str, model: str, voice: str, text: str, output_path: str) -> None:
    """Call Gemini TTS Interactions API, save audio as WAV file."""
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
        "Api-Revision": "2026-05-20",
    }
    payload = {
        "model": model,
        "input": text,
        "response_format": {"type": "audio"},
        "generation_config": {
            "speech_config": [{"voice": voice}]
        },
    }
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()

    # Extract base64 audio from response
    audio_b64 = None
    for step in data.get("steps", []):
        content = step.get("content")
        if isinstance(content, list):
            for part in content:
                if part.get("mime_type", "").startswith("audio/"):
                    audio_b64 = part.get("data")
                    break
        elif isinstance(content, dict): # fallback for other versions
            for part in content.get("parts", []):
                if part.get("inlineData", {}).get("mimeType", "").startswith("audio/"):
                    audio_b64 = part["inlineData"]["data"]
                    break
        if audio_b64:
            break

    # Fallback: check candidates structure
    if not audio_b64:
        for cand in data.get("candidates", []):
            content = cand.get("content", {})
            if isinstance(content, dict):
                for part in content.get("parts", []):
                    if part.get("inlineData", {}).get("mimeType", "").startswith("audio/"):
                        audio_b64 = part["inlineData"]["data"]
                        break
            if audio_b64:
                break

    if not audio_b64:
        raise ValueError(f"Gemini TTS: no audio data in response. Keys: {list(data.keys())}")

    pcm_bytes = base64.b64decode(audio_b64)
    wav_bytes = pcm_to_wav(pcm_bytes)
    with open(output_path, "wb") as f:
        f.write(wav_bytes)


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
    elif tts_engine == "cloning":
        voices_dir = _CLONING_DIR / "voices"
        cloned_voice_dir = voices_dir / voice
        if not voice or not cloned_voice_dir.exists() or not cloned_voice_dir.is_dir():
            raise HTTPException(status_code=400, detail=f"找不到指定的克隆聲音：{voice}")
    else:
        if voice not in ALL_VOICE_IDS:
            raise HTTPException(status_code=400, detail=f"不支援的聲音：{voice}")

    is_auto_pause = auto_pause.lower() == "true"

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
        tts_engine, gemini_tts_voice, gemini_tts_model, gemini_api_key
    )
    return {"job_id": job_id, "status": "processing"}


@app.post("/api/rescue/video-to-script")
async def rescue_video_to_script(
    file: UploadFile = File(...),
    gemini_api_key: str = Form(...),
):
    """上傳已生成的 MP4 影片，提取音軌並呼叫 Gemini API 聽寫還原為腳本文字 (.txt)。"""
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

        # 2. 提取音軌為 MP3
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

        # 使用 Gemini API 聽寫還原
        # 採用標準的 gemini-1.5-flash / gemini-2.5-flash 多模態語音處理
        url = f"https://generativelink.org/v1/chat/completions" # 採用本專案一貫的 Gemini proxy / 直接 API
        # 這邊使用現有的 call_gemini_api 邏輯或直接發送多模態 multipart/JSON
        # 由於 Gemini 官方 REST API 支援上傳檔案，或直接把音檔轉 base64 包在 Request 內
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # 選擇金鑰並呼叫
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_keys[0]
        }
        
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
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_keys[0]}"
        response = requests.post(gemini_url, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
        
        if response.status_code != 200:
            logger.error("Gemini StT failed: %s", response.text)
            raise ValueError(f"Gemini API 回傳錯誤：{response.text}")
            
        data = response.json()
        try:
            txt_content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            raise ValueError("Gemini 未能回傳有效辨識文字，請確認 API 金鑰是否正確或音質是否清晰。")

        # 4. 回傳 TXT 下載
        from fastapi.responses import Response
        output_filename = Path(file.filename).stem + "_還原腳本.txt"
        return Response(
            content=txt_content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
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


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="工作不存在。")
    return jobs[job_id]


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
):
    """Background task: TTS synthesis + video assembly."""
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

        total = len(scripts)
        clips = []
        api_keys = parse_api_keys(gemini_api_key)
        key_index = 0

        for i, text in enumerate(scripts):
            jobs[job_id]["step"] = f"第 {i + 1}/{total} 頁：生成語音旁白…"
            img_path = str(job_dir / f"page_{i:03d}.png")
            audio_ext = "wav" if tts_engine in ("gemini", "cloning") else "mp3"
            audio_path = str(job_dir / f"audio_{i:03d}.{audio_ext}")
 
            # Ensure image exists (fallback to blank)
            if not Path(img_path).exists():
                logger.warning("Image not found for page %d, skipping", i)
                continue
 
            # TTS – use placeholder if page is blank
            tts_text = text.strip() if text.strip() else "本頁無文字內容。"
 
            # Inject natural breaks at line breaks if auto_pause is enabled
            if auto_pause and text.strip():
                lines = tts_text.splitlines()
                processed_lines = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Append period if line doesn't end with sentence-ending punctuation
                    if line[-1] not in (
                        "。", "，", "、", "！", "？", "；", "：",
                        ".", ",", "!", "?", ";", ":", '"', "'", "」", "』"
                    ):
                        line += "。"
                    processed_lines.append(line)
                tts_text = " ".join(processed_lines)
 
            if tts_engine == "gemini":
                success = False
                while not success and key_index < len(api_keys):
                    current_key = api_keys[key_index]
                    try:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            executor,
                            lambda t=tts_text, p=audio_path, k=current_key: call_gemini_tts(
                                k, gemini_tts_model, gemini_tts_voice, t, p
                            )
                        )
                        success = True
                    except Exception as e:
                        if "429" in str(e) or "limit" in str(e).lower() or "quota" in str(e).lower():
                            logger.warning("Gemini TTS: Key index %d rate limited. Switching to next key...", key_index)
                            key_index += 1
                        else:
                            logger.warning("Gemini TTS: Key index %d failed: %s. Trying next key...", key_index, e)
                            key_index += 1
                if not success:
                    raise ValueError("所有提供的 Gemini API 金鑰皆已達到使用上限！無法繼續生成語音。")
            elif tts_engine == "cloning":
                import subprocess
                python_exe = str(_CLONING_DIR / ".venv" / "Scripts" / "python.exe")
                clone_script = str(_CLONING_DIR / "clone.py")
                
                cmd = [
                    python_exe, clone_script,
                    tts_text,
                    "--voice", voice,
                    "--output", str(Path(audio_path).resolve())
                ]
                
                logger.info("Page %d - Running voice cloning: %s", i + 1, cmd)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    executor,
                    lambda: subprocess.run(cmd, check=True, cwd=str(_CLONING_DIR))
                )
            else:
                communicate = edge_tts.Communicate(tts_text, voice, rate=rate)
                await communicate.save(audio_path)

            # Make 1920×1080 framed image
            framed_path = make_frame_1920x1080(img_path)

            # Build clip
            audio = AudioFileClip(audio_path)
            duration = max(audio.duration, 1.5)
            clip = ImageClip(framed_path, duration=duration).with_audio(audio)
            clips.append(clip)
            jobs[job_id]["progress"] = i + 1

        if not clips:
            raise ValueError("沒有任何可處理的頁面。")

        jobs[job_id]["step"] = "正在合成影片（可能需要數分鐘）…"

        output_path = str(job_dir / "output.mp4")
        loop = asyncio.get_event_loop()

        def write_video():
            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(
                output_path, 
                fps=5, 
                codec="libx264",
                audio_codec="aac", 
                preset="ultrafast",
                threads=4,
                logger=None
            )
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
    if backup_path.exists():
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                backup_pages = data.get("pages", [])
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

    return {"job_id": job_id, "pages": pages_data}


@app.post("/api/jobs/rebuild/{job_id}")
async def rebuild_video(job_id: str, background_tasks: BackgroundTasks):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="該專案目錄不存在。")
        
    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "total": 0,
        "step": "排隊準備重新合成...",
    }
    background_tasks.add_task(_run_rebuild, job_id)
    return {"job_id": job_id, "status": "processing"}


async def _run_rebuild(job_id: str):
    """Background task: rebuild video using existing images and audio files."""
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
        job_dir = JOBS_DIR / job_id
        
        # Determine number of pages by looking at page_xxx.png files
        img_files = sorted(list(job_dir.glob("page_*.png")))
        # Filter out _framed files to get original count
        orig_imgs = [f for f in img_files if not f.name.endswith("_framed.png")]
        total = len(orig_imgs)
        
        jobs[job_id]["total"] = total
        jobs[job_id]["step"] = "讀取現有影音檔案..."
        
        clips = []
        for i in range(total):
            jobs[job_id]["step"] = f"第 {i + 1}/{total} 頁：讀取現有影音檔案..."
            img_path = job_dir / f"page_{i:03d}_framed.png"
            if not img_path.exists():
                img_path = job_dir / f"page_{i:03d}.png"
                
            if not img_path.exists():
                logger.warning(f"Rebuild: page_{i:03d} image not found.")
                continue
                
            # Ensure it is letterboxed to 1920x1080
            framed_path = img_path
            if not img_path.name.endswith("_framed.png"):
                framed_path = Path(make_frame_1920x1080(str(img_path)))
                
            # Find audio (.mp3 or .wav)
            audio_path = job_dir / f"audio_{i:03d}.mp3"
            if not audio_path.exists():
                audio_path = job_dir / f"audio_{i:03d}.wav"
                
            if not audio_path.exists():
                logger.warning(f"Rebuild: audio_{i:03d} not found.")
                continue
                
            audio = AudioFileClip(str(audio_path))
            duration = max(audio.duration, 1.5)
            clip = ImageClip(str(framed_path), duration=duration).with_audio(audio)
            clips.append(clip)
            jobs[job_id]["progress"] = i + 1
            
        if not clips:
            raise ValueError("找不到任何可配對的投影片與配音檔組合。")
            
        jobs[job_id]["step"] = "正在重新合成影片（可能需要數分鐘）..."
        output_path = str(job_dir / "output.mp4")
        
        loop = asyncio.get_event_loop()
        def write_video():
            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(
                output_path, 
                fps=5, 
                codec="libx264",
                audio_codec="aac", 
                preset="ultrafast",
                threads=4,
                logger=None
            )
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8003, reload=False)
