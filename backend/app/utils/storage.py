"""Storage and path management utilities."""

import re
import unicodedata
from pathlib import Path
from app.config import settings


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and shell injection."""
    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    # Remove undesirable chars
    filename = re.sub(r"[^\w\s\.-]", "", filename).strip()
    # Replace whitespace with underscore
    filename = re.sub(r"\s+", "_", filename)
    return filename or "unnamed_video"


def get_media_url(file_path: str | Path | None) -> str | None:
    """Convert an absolute or relative path inside data dir into an API media stream URL."""
    if not file_path:
        return None
    path = Path(file_path)
    # Return endpoint relative path
    try:
        rel_path = path.relative_to(settings.DATA_DIR)
        return f"/api/media/{rel_path.as_posix()}"
    except ValueError:
        return f"/api/media/{path.name}"
