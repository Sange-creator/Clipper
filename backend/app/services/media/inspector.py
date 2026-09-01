"""Media inspector utilizing ffprobe for technical metadata extraction and validation."""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.config import settings
from app.core.exceptions import MediaValidationError

logger = logging.getLogger(__name__)


class MediaMetadata(BaseModel):
    """Normalized technical metadata for a video file."""
    duration_seconds: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str
    bitrate: int
    file_size_bytes: int
    has_audio: bool
    aspect_ratio: str
    rotation: int = 0
    raw_streams: Dict[str, Any] = {}


class MediaInspector:
    """Inspects and validates media files using ffprobe."""

    def __init__(self):
        self.ffprobe_path = shutil.which("ffprobe") or "ffprobe"

    async def inspect(self, file_path: Path | str) -> MediaMetadata:
        """Run ffprobe on the target file and parse JSON metadata."""
        path = Path(file_path)
        if not path.exists():
            raise MediaValidationError(f"File not found: {file_path}")

        # Check extension
        ext = path.suffix.lower()
        if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
            raise MediaValidationError(f"Unsupported file extension: {ext}. Allowed: {settings.ALLOWED_VIDEO_EXTENSIONS}")

        file_size = path.stat().st_size
        if file_size == 0:
            raise MediaValidationError("File is empty (0 bytes).")
        if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise MediaValidationError(f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-print_format", "json",
            str(path.resolve())
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise MediaValidationError(f"ffprobe failed: {stderr.decode('utf-8', errors='ignore')}")

            data = json.loads(stdout.decode("utf-8"))
        except Exception as e:
            raise MediaValidationError(f"Failed to inspect media file: {e}")

        # Parse streams
        video_stream = None
        audio_stream = None
        for stream in data.get("streams", []):
            codec_type = stream.get("codec_type")
            if codec_type == "video" and video_stream is None:
                video_stream = stream
            elif codec_type == "audio" and audio_stream is None:
                audio_stream = stream

        if not video_stream:
            raise MediaValidationError("Uploaded file contains no valid video stream.")

        format_info = data.get("format", {})
        duration = float(format_info.get("duration", video_stream.get("duration", 0.0)))
        if duration <= 1.0:
            raise MediaValidationError("Video duration is too short (< 1 second).")

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        if width == 0 or height == 0:
            raise MediaValidationError("Invalid video dimensions detected.")

        # Calculate FPS
        fps = 30.0
        r_frame_rate = video_stream.get("r_frame_rate", "30/1")
        if "/" in r_frame_rate:
            num, den = r_frame_rate.split("/")
            if float(den) > 0:
                fps = round(float(num) / float(den), 2)

        # Check rotation tags
        rotation = 0
        side_data = video_stream.get("side_data_list", [])
        for sd in side_data:
            if "rotation" in sd:
                rotation = int(sd["rotation"])
        if "tags" in video_stream and "rotate" in video_stream["tags"]:
            rotation = int(video_stream["tags"]["rotate"])

        # Normalize rotation
        if rotation in (90, 270, -90, -270):
            width, height = height, width

        bitrate = int(format_info.get("bit_rate", video_stream.get("bit_rate", 0)))
        video_codec = video_stream.get("codec_name", "unknown")
        audio_codec = audio_stream.get("codec_name", "") if audio_stream else ""
        has_audio = audio_stream is not None

        aspect_ratio = f"{width}:{height}"
        if width > 0 and height > 0:
            gcd_val = self._gcd(width, height)
            aspect_ratio = f"{width // gcd_val}:{height // gcd_val}"

        return MediaMetadata(
            duration_seconds=round(duration, 2),
            width=width,
            height=height,
            fps=fps,
            video_codec=video_codec,
            audio_codec=audio_codec,
            bitrate=bitrate,
            file_size_bytes=file_size,
            has_audio=has_audio,
            aspect_ratio=aspect_ratio,
            rotation=rotation,
            raw_streams=data
        )

    def _gcd(self, a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a


inspector = MediaInspector()
