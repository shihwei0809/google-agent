import json
from pathlib import Path

from app.core.config import settings
from app.models.schemas import StoryboardFrame
from app.utils.command_utils import run_command


class VideoService:
    """Use FFmpeg to turn generated images into a subtitled MP4 with background music."""

    def create_video_from_images(
        self,
        frames: list[StoryboardFrame],
        image_paths: list[Path],
        subtitle_path: Path,
        background_music_path: Path,
        work_dir: Path,
    ) -> Path:
        if not image_paths:
            raise ValueError("找不到可用圖片，無法合成影片。")
        if len(frames) != len(image_paths):
            raise ValueError("分鏡資料與圖片數量不一致，無法合成影片。")
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕檔不存在: {subtitle_path}")
        if not background_music_path.exists():
            raise FileNotFoundError(f"背景音樂不存在: {background_music_path}")

        concat_list = work_dir / "images.txt"
        temp_video = work_dir / "video_no_audio.mp4"
        final_video = work_dir / "final_video.mp4"

        concat_lines: list[str] = []
        for frame, image_path in zip(frames, image_paths, strict=False):
            concat_lines.append(f"file '{image_path.resolve().as_posix()}'")
            concat_lines.append(f"duration {frame.duration_seconds}")

        concat_lines.append(f"file '{image_paths[-1].resolve().as_posix()}'")
        concat_list.write_text("\n".join(concat_lines), encoding="utf-8")

        subtitles_filter = self._build_subtitle_filter(subtitle_path)

        run_command(
            [
                settings.ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-vf",
                subtitles_filter,
                "-vsync",
                "vfr",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                str(temp_video),
            ]
        )

        video_duration = self._probe_duration(temp_video)

        run_command(
            [
                settings.ffmpeg_path,
                "-y",
                "-i",
                str(temp_video),
                "-stream_loop",
                "-1",
                "-i",
                str(background_music_path),
                "-t",
                str(video_duration),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(final_video),
            ]
        )

        return final_video

    def _probe_duration(self, video_path: Path) -> float:
        result = run_command(
            [
                settings.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(video_path),
            ],
            capture_output=True,
        )
        payload = json.loads(result.stdout)
        duration = float(payload["format"]["duration"])
        if duration <= 0:
            raise ValueError("FFprobe 取得的影片長度無效。")
        return duration

    @staticmethod
    def _build_subtitle_filter(subtitle_path: Path) -> str:
        normalized = subtitle_path.resolve().as_posix().replace(":", "\\:")
        return f"subtitles='{normalized}'"
