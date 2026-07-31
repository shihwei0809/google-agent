from pydantic import BaseModel, Field, field_validator


class GenerateVideoRequest(BaseModel):
    """Incoming form fields for the video generation job."""

    topic: str = Field(..., min_length=1, max_length=200)
    scene: str = Field(..., min_length=1, max_length=200)
    character: str = Field(..., min_length=1, max_length=200)
    storyboard_markdown: str | None = Field(default=None, max_length=40000)

    @field_validator("topic", "scene", "character")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("輸入欄位不可為空白。")
        return cleaned

    @field_validator("storyboard_markdown")
    @classmethod
    def normalize_storyboard_markdown(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class GenerateVideoResponse(BaseModel):
    """API response describing the finished video artifact."""

    job_id: str
    video_path: str
    subtitle_path: str
    drive_file_id: str
    drive_link: str


class StoryboardFrame(BaseModel):
    """A single frame prompt and subtitle entry."""

    index: int
    image_prompt: str
    subtitle_text: str
    duration_seconds: float = Field(default=3.0, gt=0)

