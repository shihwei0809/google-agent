import logging
import mimetypes
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Upload the final MP4 to Google Drive and return a shareable link."""

    def __init__(self) -> None:
        self.scopes = ["https://www.googleapis.com/auth/drive"]

    def is_configured(self) -> bool:
        folder_id = settings.google_drive_folder_id.strip()
        credentials_ok = settings.credentials_path.exists()
        folder_ok = bool(folder_id and folder_id != "your_google_drive_folder_id")
        return credentials_ok and folder_ok

    def upload_video(self, video_path: Path) -> dict[str, str]:
        if not video_path.exists():
            raise FileNotFoundError(f"待上傳影片不存在: {video_path}")
        if not self.is_configured():
            raise FileNotFoundError("Google Drive 憑證或資料夾 ID 尚未設定完成。")

        credentials = service_account.Credentials.from_service_account_file(
            str(settings.credentials_path),
            scopes=self.scopes,
        )
        service = build("drive", "v3", credentials=credentials, cache_discovery=False)

        mime_type = mimetypes.guess_type(video_path.name)[0] or "video/mp4"
        metadata = {
            "name": video_path.name,
            "parents": [settings.google_drive_folder_id],
        }
        media = MediaFileUpload(str(video_path), mimetype=mime_type, resumable=True)

        file_data = (
            service.files()
            .create(body=metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )

        service.permissions().create(
            fileId=file_data["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()

        web_view_link = file_data.get("webViewLink") or (
            f"https://drive.google.com/file/d/{file_data['id']}/view?usp=sharing"
        )
        logger.info("Uploaded video to Google Drive: %s", web_view_link)
        return {
            "id": file_data["id"],
            "link": web_view_link,
        }
