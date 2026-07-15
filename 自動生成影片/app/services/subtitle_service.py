from pathlib import Path

from app.models.schemas import StoryboardFrame


class SubtitleService:
    """Create an SRT file aligned with the generated frames."""

    def create_srt(self, frames: list[StoryboardFrame], output_path: Path) -> Path:
        lines: list[str] = []
        current_seconds = 0.0

        for frame in frames:
            start_seconds = current_seconds
            end_seconds = current_seconds + frame.duration_seconds
            current_seconds = end_seconds

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
    def _format_timestamp(total_seconds: float) -> str:
        total_milliseconds = round(total_seconds * 1000)
        hours = total_milliseconds // 3_600_000
        minutes = (total_milliseconds % 3_600_000) // 60_000
        seconds = (total_milliseconds % 60_000) // 1000
        milliseconds = total_milliseconds % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
