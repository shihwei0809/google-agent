from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import GenerateVideoRequest, GenerateVideoResponse
from app.services.pipeline_service import VideoGenerationPipeline

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
