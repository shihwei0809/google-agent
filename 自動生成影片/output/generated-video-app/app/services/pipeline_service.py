import logging
from pathlib import Path

from app.core.config import settings
from app.models.schemas import GenerateVideoRequest
from app.services.drive_service import GoogleDriveService
from app.services.openai_service import OpenAIImageService
from app.services.subtitle_service import SubtitleService
from app.services.video_service import VideoService
from app.utils.file_utils import ensure_directory, make_job_id

logger = logging.getLogger(__name__)


class VideoGenerationPipeline:
    """Coordinate the full video generation workflow."""

    def __init__(self) -> None:
        self.image_service = OpenAIImageService()
        self.subtitle_service = SubtitleService()
        self.video_service = VideoService()
        self.drive_service = GoogleDriveService()

    def run(self, request: GenerateVideoRequest) -> dict[str, str | None]:
        ensure_directory(settings.output_dir)

        job_id = make_job_id()
        job_dir = ensure_directory(settings.output_dir / job_id)
        image_dir = ensure_directory(job_dir / "images")

        logger.info("Starting job %s", job_id)

        frames = self.image_service.build_storyboard(request)
        image_paths = self.image_service.generate_images(frames, image_dir)

        subtitle_path = self.subtitle_service.create_srt(
            frames=frames,
            output_path=job_dir / "subtitles.srt",
        )

        background_audio_path = self._resolve_background_audio(job_dir)

        final_video_path = self.video_service.create_video_from_images(
            frames=frames,
            image_paths=image_paths,
            subtitle_path=subtitle_path,
            background_music_path=background_audio_path,
            work_dir=job_dir,
        )

        drive_file_id: str | None = None
        drive_link: str | None = None
        if self.drive_service.is_configured():
            upload_result = self.drive_service.upload_video(final_video_path)
            drive_file_id = upload_result["id"]
            drive_link = upload_result["link"]
        else:
            logger.info(
                "Google Drive upload skipped because credentials or folder ID are not configured."
            )

        logger.info("Completed job %s", job_id)
        return {
            "job_id": job_id,
            "video_path": str(final_video_path),
            "subtitle_path": str(subtitle_path),
            "drive_file_id": drive_file_id,
            "drive_link": drive_link,
        }

    def _resolve_background_audio(self, job_dir: Path) -> Path:
        configured_path = settings.background_music_file
        if configured_path.exists():
            return configured_path

        silent_audio_path = job_dir / "generated_silence.mp3"
        logger.info(
            "Background music not found at %s. Generating silent fallback audio.",
            configured_path,
        )
        self.video_service.create_silent_audio(
            output_path=silent_audio_path,
            duration_seconds=600,
        )
        return silent_audio_path
