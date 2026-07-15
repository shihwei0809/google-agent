import logging
import re
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, status, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import fitz
from google import genai

from app.core.config import settings
from app.models.schemas import GenerateVideoRequest, GenerateVideoResponse
from app.services.pipeline_service import VideoGenerationPipeline

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
pipeline = VideoGenerationPipeline()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render a simple form for collecting video generation inputs."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.post(
    "/generate-video",
    response_model=GenerateVideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_video(
    topic: str = Form(...),
    scene: str = Form(...),
    character: str = Form(...),
    storyboard_markdown: str = Form(default=""),
) -> GenerateVideoResponse:
    """Generate a video end-to-end and return the Google Drive link."""
    payload = GenerateVideoRequest(
        topic=topic,
        scene=scene,
        character=character,
        storyboard_markdown=storyboard_markdown,
    )

    try:
        result = pipeline.run(payload)
        return GenerateVideoResponse(
            job_id=result["job_id"],
            video_path=str(Path(result["video_path"]).as_posix()),
            subtitle_path=str(Path(result["subtitle_path"]).as_posix()),
            drive_file_id=result["drive_file_id"],
            drive_link=result["drive_link"],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"影片生成流程失敗: {exc}",
        ) from exc


@router.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    """Parse text from PDF and generate a structured storyboard table using Gemini."""
    try:
        # Read file contents
        contents = await file.read()
        
        # Open PDF from memory bytes using PyMuPDF
        doc = fitz.open(stream=contents, filetype="pdf")
        full_text = ""
        for i, page in enumerate(doc):
            full_text += f"\n--- Page {i+1} ---\n"
            full_text += page.get_text()
            
        if not full_text.strip():
            raise HTTPException(status_code=400, detail="PDF 中未包含可讀取的文字。")
            
        # Initialize Google GenAI client using configured key
        client = genai.Client(api_key=settings.google_api_key)
        
        prompt = (
            "你是一個專業的影片分鏡編劇。以下是從教育訓練簡報 PDF 萃取出的文字內容。\n"
            "請將這些文字整理成一個適合製作成教育訓練影片的「分鏡腳本」Markdown 表格。\n"
            "表格必須嚴格包含以下欄位：\n"
            "| 場次 | 景別 | 時間秒數 | 畫面內容說明 | 角色動作 | 音效 | AI 生圖提示詞 |\n\n"
            "格式說明：\n"
            "1. 「時間秒數」欄位請填寫估計此幕需要的秒數，如 `3`（代表這一鏡播放 3 秒）。\n"
            "2. 「AI 生圖提示詞」非常重要！請用【英文】撰寫，必須是詳細、具電影感(cinematic)、攝影風格與視覺連續性(visual continuity)的繪圖 prompt，用於 DALL-E/Imagen 繪圖。\n"
            "3. 畫面內容說明、角色動作、音效請用【繁體中文】。\n"
            "4. 請根據簡報內容，切分成大約 10~25 鏡的合理分鏡即可。\n"
            "5. 請只回傳 Markdown 表格，不要包含 ```markdown 標記或任何額外說明，表格內容必須嚴格對齊，不要有前後多餘的文字。\n\n"
            "簡報文字內容：\n"
            f"{full_text}"
        )
        
        # Use gemini-2.5-flash for fast text generation
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        
        markdown_table = response.text.strip()
        
        # Simple heuristic to clean up any markdown code blocks returned by LLM
        if markdown_table.startswith("```"):
            markdown_table = re.sub(r"^```[a-zA-Z]*\n", "", markdown_table)
            markdown_table = re.sub(r"\n```$", "", markdown_table)
            markdown_table = markdown_table.strip()
            
        # Try to guess a topic from the first page's text
        topic = ""
        first_page_text = doc[0].get_text()
        first_lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
        if first_lines:
            topic = first_lines[0]
            if len(topic) > 30:
                topic = topic[:30] + "..."
                
        return {
            "status": "success",
            "topic": topic,
            "storyboard": markdown_table
        }
        
    except Exception as e:
        logger.exception("PDF parsing or Gemini prompt failed")
        raise HTTPException(
            status_code=500,
            detail=f"PDF 解析或 AI 生成腳本失敗: {e}"
        )
