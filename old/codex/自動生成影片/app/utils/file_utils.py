from datetime import datetime
from pathlib import Path
from uuid import uuid4


def ensure_directory(path: Path) -> Path:
    """Create a directory when it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_required_file(path: Path, label: str) -> None:
    """Fail early when a required file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"{label}檔案不存在: {path}")


def make_job_id() -> str:
    """Create a compact job id suitable for folder names."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:8]
    return f"{timestamp}_{suffix}"
