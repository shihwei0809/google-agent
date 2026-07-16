from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = Field(default="AI自動影片生成系統", alias="PROJECT_NAME")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    image_provider: str = Field(default="google_gemini", alias="IMAGE_PROVIDER")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_image_model: str = Field(
        default="gemini-2.5-flash-image",
        alias="GOOGLE_IMAGE_MODEL",
    )

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_image_model: str = Field(default="gpt-image-2", alias="OPENAI_IMAGE_MODEL")
    openai_image_size: str = Field(default="1536x1024", alias="OPENAI_IMAGE_SIZE")
    openai_image_quality: str = Field(default="medium", alias="OPENAI_IMAGE_QUALITY")

    google_drive_service_account_file: str = Field(
        alias="GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE"
    )
    google_drive_folder_id: str = Field(alias="GOOGLE_DRIVE_FOLDER_ID")

    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    ffprobe_path: str = Field(default="ffprobe", alias="FFPROBE_PATH")
    image_count: int = Field(default=50, alias="IMAGE_COUNT")
    seconds_per_image: int = Field(default=3, alias="SECONDS_PER_IMAGE")
    background_music_path: str = Field(
        default="assets/background_music.mp3",
        alias="BACKGROUND_MUSIC_PATH",
    )

    @property
    def output_dir(self) -> Path:
        return Path("output")

    @property
    def credentials_path(self) -> Path:
        return Path(self.google_drive_service_account_file)

    @property
    def background_music_file(self) -> Path:
        return Path(self.background_music_path)


settings = Settings()
