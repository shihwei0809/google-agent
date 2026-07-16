import base64
import logging
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
        """Create 50 deterministic prompts so the pipeline works without extra LLM calls."""
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
                )
            )

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
