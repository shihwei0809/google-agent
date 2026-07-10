"""
PDF 語音旁白影片生成器
流程：上傳 PDF → 讀取腳本 → 人工檢視修正 → 選擇語音 → 生成影片
"""
import asyncio
import base64
import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
    r"C:\Users\C606-PC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe",
)
if Path(FFMPEG_PATH).exists():
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

JOBS_DIR = Path("jobs")
JOBS_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
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

# ─── Helpers ──────────────────────────────────────────────────────────────────

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


@app.post("/api/extract")
def extract_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="請上傳 PDF 格式的檔案。")

    job_id = str(uuid.uuid4())
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
    for i, page in enumerate(doc):
        text = page.get_text().strip()

        # High-res PNG for video assembly
        mat_hi = fitz.Matrix(2, 2)
        pix_hi = page.get_pixmap(matrix=mat_hi)
        pix_hi.save(str(job_dir / f"page_{i:03d}.png"))

        # Thumbnail for browser preview (35%)
        mat_th = fitz.Matrix(0.35, 0.35)
        pix_th = page.get_pixmap(matrix=mat_th)
        thumb_path = job_dir / f"thumb_{i:03d}.png"
        pix_th.save(str(thumb_path))

        pages_data.append({
            "page_num": i + 1,
            "text": text,
            "thumbnail": f"/jobs/{job_id}/thumb_{i:03d}.png",
        })

    jobs[job_id] = {"status": "extracted", "total_pages": len(pages_data)}
    logger.info("Extracted %d pages, job=%s", len(pages_data), job_id)
    return {"job_id": job_id, "pages": pages_data}


@app.post("/api/generate")
async def generate_video(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    scripts: str = Form(...),
    voice: str = Form(...),
):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="工作不存在，請重新上傳 PDF。")

    try:
        scripts_list: list[str] = json.loads(scripts)
    except Exception:
        raise HTTPException(status_code=400, detail="腳本格式錯誤。")

    if voice not in ALL_VOICE_IDS:
        raise HTTPException(status_code=400, detail=f"不支援的聲音：{voice}")

    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "total": len(scripts_list),
        "step": "準備中…",
    }
    background_tasks.add_task(_run_generation, job_id, scripts_list, voice, job_dir)
    return {"job_id": job_id, "status": "processing"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="工作不存在。")
    return jobs[job_id]


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


async def _run_generation(job_id: str, scripts: list[str], voice: str, job_dir: Path):
    """Background task: TTS synthesis + video assembly."""
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

        total = len(scripts)
        clips = []

        for i, text in enumerate(scripts):
            jobs[job_id]["step"] = f"第 {i + 1}/{total} 頁：生成語音旁白…"
            img_path = str(job_dir / f"page_{i:03d}.png")
            audio_path = str(job_dir / f"audio_{i:03d}.mp3")

            # Ensure image exists (fallback to blank)
            if not Path(img_path).exists():
                logger.warning("Image not found for page %d, skipping", i)
                continue

            # TTS – use placeholder if page is blank
            tts_text = text.strip() if text.strip() else "本頁無文字內容。"
            communicate = edge_tts.Communicate(tts_text, voice)
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
            final.write_videofile(output_path, fps=24, audio_codec="aac", logger=None)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=False)
