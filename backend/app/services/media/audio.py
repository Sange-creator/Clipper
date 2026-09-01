"""Audio extraction and normalization service using FFmpeg."""

import asyncio
import logging
import shutil
from pathlib import Path
from app.core.exceptions import MediaProcessingError

logger = logging.getLogger(__name__)


class AudioService:
    """Extracts 16kHz mono WAV for Whisper speech recognition and normalizes audio levels."""

    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

    async def extract_whisper_audio(self, video_path: Path | str, output_wav_path: Path | str) -> Path:
        """Extract 16kHz mono 16-bit PCM WAV audio optimized for Whisper models."""
        in_path = Path(video_path)
        out_path = Path(output_wav_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(in_path.resolve()),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(out_path.resolve())
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="ignore")
            logger.error(f"FFmpeg audio extraction failed: {err_msg}")
            raise MediaProcessingError(f"Audio extraction failed: {err_msg}")

        return out_path


audio_service = AudioService()
