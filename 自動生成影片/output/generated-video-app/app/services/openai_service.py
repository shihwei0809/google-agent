import base64
import logging
import re
from pathlib import Path

from google import genai

from app.core.config import settings
from app.models.schemas import GenerateVideoRequest, StoryboardFrame

logger = logging.getLogger(__name__)


class OpenAIImageService:
    """Generate storyboard prompts and images with the configured image provider."""

    def __init__(self) -> None:
        if settings.image_provider != "google_gemini":
            raise ValueError(
                f"Unsupported IMAGE_PROVIDER: {settings.image_provider}. "
                "Expected 'google_gemini'."
            )
        self.client = genai.Client(api_key=settings.google_api_key)

    def build_storyboard(self, request: GenerateVideoRequest) -> list[StoryboardFrame]:
        """Build frames from a markdown table when provided, else use the default generator."""
        if request.storyboard_markdown:
            return self._build_storyboard_from_markdown(request)
        return self._build_default_storyboard(request)

    def _build_default_storyboard(
        self,
        request: GenerateVideoRequest,
    ) -> list[StoryboardFrame]:
        frames: list[StoryboardFrame] = []
        for index in range(settings.image_count):
            sequence_no = index + 1
            prompt = (
                f"Create a cinematic storyboard frame for '{request.topic}', set in "
                f"'{request.scene}', featuring '{request.character}'. Frame {sequence_no} of "
                f"{settings.image_count}. Keep visual continuity, realistic lighting, and a "
                f"polished commercial look."
            )
            frames.append(
                StoryboardFrame(
                    index=sequence_no,
                    image_prompt=prompt,
                    subtitle_text=(
                        f"第 {sequence_no} 幕：{request.character} 在 {request.scene} 中，"
                        f"圍繞「{request.topic}」展開故事。"
                    ),
                    duration_seconds=float(settings.seconds_per_image),
                    shot_size="預設景別",
                    camera_move="slow push in",
                    visual_description=request.scene,
                    role_action=request.character,
                    music_tempo="steady beat",
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
            prompt = self._get_column(row, "AI 生圖提示詞", "AI生圖提示詞", "prompt")
            if not prompt:
                raise ValueError(f"第 {index} 筆分鏡缺少 AI 生圖提示詞。")

            scene_no = self._get_column(row, "場次", "scene_no") or str(index)
            shot_size = self._get_column(row, "景別", "shot_size")
            shot_time = self._get_column(row, "時間秒數", "duration")
            focal_length = self._get_column(row, "焦段", "focal_length")
            camera_angle = self._get_column(row, "機位角度", "camera_angle")
            camera_move = self._get_column(row, "機位運動", "camera_move")
            visual_desc = self._get_column(row, "畫面內容說明", "visual_description")
            composition = self._get_column(row, "構圖說明", "composition")
            role_action = self._get_column(row, "角色動作", "role_action")
            motion_line = self._get_column(row, "鏡頭運動指示線描述", "motion_line")
            lighting = self._get_column(row, "光線與色調", "lighting")
            sound_effect = self._get_column(row, "音效", "sound_effect")
            music_tempo = self._get_column(row, "配樂節奏", "music_tempo")

            subtitle_parts = [
                f"場次 {scene_no}",
                shot_size,
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
                    shot_size=shot_size,
                    focal_length=focal_length,
                    camera_angle=camera_angle,
                    camera_move=camera_move,
                    visual_description=visual_desc,
                    composition=composition,
                    role_action=role_action,
                    motion_line=motion_line,
                    lighting=lighting,
                    sound_effect=sound_effect,
                    music_tempo=music_tempo,
                )
            )

        return frames

    def generate_images(
        self,
        frames: list[StoryboardFrame],
        image_dir: Path,
    ) -> list[Path]:
        """Generate one image per storyboard frame and save each image to disk."""
        if not settings.google_api_key.strip():
            raise ValueError("尚未設定 GOOGLE_API_KEY，無法使用 Google Gemini 生成圖片。")

        image_paths: list[Path] = []
        for frame in frames:
            logger.info(
                "Generating image %s/%s with %s",
                frame.index,
                len(frames),
                settings.google_image_model,
            )
            response = self.client.models.generate_content(
                model=settings.google_image_model,
                contents=[frame.image_prompt],
            )

            image_bytes = self._extract_first_image_bytes(response)
            if not image_bytes:
                raise ValueError(f"Google Gemini 未回傳第 {frame.index} 張圖片資料。")

            image_path = image_dir / f"frame_{frame.index:03d}.png"
            image_path.write_bytes(image_bytes)
            image_paths.append(image_path)

        return image_paths

    @staticmethod
    def _extract_first_image_bytes(response: object) -> bytes | None:
        parts = []
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content and getattr(content, "parts", None):
                parts.extend(content.parts)
        if not parts and getattr(response, "parts", None):
            parts = list(response.parts)

        for part in parts:
            inline_data = getattr(part, "inline_data", None)
            if not inline_data:
                continue
            data = getattr(inline_data, "data", None)
            if isinstance(data, bytes):
                return data
            if isinstance(data, str):
                return base64.b64decode(data)
        return None

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
