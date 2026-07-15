import base64
import logging
import re
from pathlib import Path

from openai import OpenAI

from app.core.config import settings
from app.models.schemas import GenerateVideoRequest, StoryboardFrame

logger = logging.getLogger(__name__)


class OpenAIImageService:
    """Generate storyboard prompts and images with the OpenAI Image API."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def build_storyboard(self, request: GenerateVideoRequest) -> list[StoryboardFrame]:
        """Build frames from a markdown table when provided, else use the default generator."""
        if request.storyboard_markdown:
            return self._build_storyboard_from_markdown(request)
        return self._build_default_storyboard(request)

    def _build_default_storyboard(
        self,
        request: GenerateVideoRequest,
    ) -> list[StoryboardFrame]:
        camera_styles = [
            "wide cinematic shot",
            "medium shot",
            "close-up portrait shot",
            "overhead shot",
            "tracking shot",
            "dramatic side angle",
            "establishing shot",
            "emotional close-up",
            "dynamic motion shot",
            "symmetrical centered shot",
        ]
        lighting_styles = [
            "golden-hour lighting",
            "soft natural lighting",
            "dramatic rim lighting",
            "studio-quality key light",
            "misty ambient light",
        ]
        moods = [
            "hopeful",
            "inspiring",
            "vivid",
            "adventurous",
            "warm",
        ]

        frames: list[StoryboardFrame] = []
        for index in range(settings.image_count):
            camera = camera_styles[index % len(camera_styles)]
            lighting = lighting_styles[index % len(lighting_styles)]
            mood = moods[index % len(moods)]
            sequence_no = index + 1

            prompt = (
                f"Create a high-quality cinematic storyboard image for a video about "
                f"'{request.topic}'. The main scene is '{request.scene}'. The main character is "
                f"'{request.character}'. Frame {sequence_no} of {settings.image_count}. "
                f"Use a {camera}, {lighting}, and a {mood} mood. Keep visual continuity across "
                f"all frames, preserve the same character identity, and make the frame suitable "
                f"for a polished promotional short film."
            )
            subtitle = (
                f"第 {sequence_no} 幕：{request.character} 在 {request.scene} 中，"
                f"圍繞「{request.topic}」展開故事。"
            )

            frames.append(
                StoryboardFrame(
                    index=sequence_no,
                    image_prompt=prompt,
                    subtitle_text=subtitle,
                    duration_seconds=float(settings.seconds_per_image),
                )
            )

        return frames

    def _build_storyboard_from_markdown(
        self,
        request: GenerateVideoRequest,
    ) -> list[StoryboardFrame]:
        rows = self._parse_markdown_table(request.storyboard_markdown or "")
        if not rows:
            raise ValueError("分鏡表格式無法解析，請貼上標準 Markdown 表格。")

        frames: list[StoryboardFrame] = []
        for index, row in enumerate(rows, start=1):
            prompt = self._get_column(
                row,
                "AI 生圖提示詞",
                "AI生圖提示詞",
                "prompt",
            )
            if not prompt:
                raise ValueError(f"第 {index} 筆分鏡缺少 AI 生圖提示詞。")

            scene_no = self._get_column(row, "場次") or str(index)
            shot_type = self._get_column(row, "景別") or "未指定景別"
            shot_time = self._get_column(row, "時間秒數") or ""
            visual_desc = self._get_column(row, "畫面內容說明") or ""
            role_action = self._get_column(row, "角色動作") or ""
            sound_desc = self._get_column(row, "音效") or ""

            subtitle_parts = [
                f"場次 {scene_no}",
                shot_type,
                visual_desc,
                role_action,
            ]
            subtitle_text = "，".join(part for part in subtitle_parts if part)

            frames.append(
                StoryboardFrame(
                    index=index,
                    image_prompt=prompt,
                    subtitle_text=subtitle_text,
                    duration_seconds=self._parse_duration_seconds(shot_time),
                )
            )

            if sound_desc:
                logger.info("Storyboard frame %s sound cue: %s", index, sound_desc)

        return frames

    def generate_images(
        self,
        frames: list[StoryboardFrame],
        image_dir: Path,
    ) -> list[Path]:
        """Generate one image per storyboard frame and save each image to disk."""
        image_paths: list[Path] = []

        for frame in frames:
            logger.info("Generating image %s/%s", frame.index, len(frames))
            result = self.client.images.generate(
                model=settings.openai_image_model,
                prompt=frame.image_prompt,
                size=settings.openai_image_size,
                quality=settings.openai_image_quality,
            )

            if not result.data or not result.data[0].b64_json:
                raise ValueError(f"OpenAI 未回傳第 {frame.index} 張圖片資料。")

            image_bytes = base64.b64decode(result.data[0].b64_json)
            image_path = image_dir / f"frame_{frame.index:03d}.png"
            image_path.write_bytes(image_bytes)
            image_paths.append(image_path)

        return image_paths

    @staticmethod
    def _parse_markdown_table(markdown: str) -> list[dict[str, str]]:
        lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
        if len(table_lines) < 3:
            return []

        headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
        rows: list[dict[str, str]] = []

        for raw_line in table_lines[2:]:
            cells = [cell.strip() for cell in raw_line.strip("|").split("|")]
            if len(cells) != len(headers):
                continue
            rows.append(dict(zip(headers, cells, strict=False)))

        return rows

    @staticmethod
    def _get_column(row: dict[str, str], *names: str) -> str:
        for name in names:
            value = row.get(name)
            if value:
                return value.strip()
        return ""

    @staticmethod
    def _parse_duration_seconds(value: str) -> float:
        matches = re.findall(r"\d+(?:\.\d+)?", value)
        if len(matches) >= 2:
            start = float(matches[0])
            end = float(matches[1])
            if end > start:
                return round(end - start, 3)
        return float(settings.seconds_per_image)
