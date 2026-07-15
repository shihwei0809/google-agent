from pathlib import Path

from app.core.config import settings
from app.models.schemas import StoryboardFrame


class SubtitleService:
    """Create an SRT file aligned with the generated frames."""

    def create_srt(self, frames: list[StoryboardFrame], output_path: Path) -> Path:
        lines: list[str] = []

        for frame in frames:
            start_seconds = (frame.index - 1) * settings.seconds_per_image
            end_seconds = frame.index * settings.seconds_per_image

            lines.extend(
                [
                    str(frame.index),
                    (
                        f"{self._format_timestamp(start_seconds)} --> "
                        f"{self._format_timestamp(end_seconds)}"
                    ),
                    frame.subtitle_text,
                    "",
                ]
            )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    @staticmethod
    def _format_timestamp(total_seconds: int) -> str:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"
