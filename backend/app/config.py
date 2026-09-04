"""Configuration module for AI Video Clipper."""

from pathlib import Path
from typing import Dict, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Application Settings loaded from environment or defaults."""
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "AI Video Clipper"
    APP_ENV: Literal["development", "production", "test"] = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Storage paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    THUMBNAIL_DIR: Path = DATA_DIR / "thumbnails"
    SUBTITLE_DIR: Path = DATA_DIR / "subtitles"

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'clipper.db'}"

    # AI Configuration
    AI_PROVIDER: str = "gemini"  # "gemini", "groq", or "mock"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # Transcription Configuration (Deepgram & Faster-Whisper)
    DEEPGRAM_API_KEY: str = ""
    DEEPGRAM_MODEL: str = "nova-3"  # "nova-3", "nova-2", "nova-2-conversational", "nova-2-meeting"
    TRANSCRIBER_PROVIDER: str = "auto"  # "auto", "deepgram", "whisper"
    WHISPER_MODEL_SIZE: str = "base"  # "tiny", "base", "small", "medium", "large-v3"
    WHISPER_DEVICE: str = "cpu"  # "cpu", "cuda", "mps"

    # Media Limits & Processing (0 = Unlimited file size, supports any video size)
    MAX_UPLOAD_SIZE_MB: int = 0
    ALLOWED_VIDEO_EXTENSIONS: list[str] = [".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"]
    DEFAULT_OUTPUT_ASPECT_RATIO: str = "9:16"
    DEFAULT_FRAMING_MODE: str = "crop_9_16"  # "crop_9_16", "blur_fit_9_16", "original_16_9"
    DEFAULT_BLUR_RADIUS: int = 30  # 10 (Light), 30 (Medium), 50 (Heavy), 80 (Ultra)
    DEFAULT_SUBTITLE_POSITION: int = 75  # 10% (Top) to 90% (Bottom), default 75% (Lower-Third)
    DEFAULT_ADD_HOOK_HEADER: bool = False  # Add sticky persistent TikTok hook title throughout video
    DEFAULT_HOOK_HEADER_POSITION: int = 12  # 8% (Top Banner) to 90% (Bottom), default 12%
    DEFAULT_HOOK_HEADER_STYLE: str = "viral_creator"  # "viral_creator", "white_box", "meme", "nostalgic", "old_history", "neon_cyber"
    DEFAULT_REMOVE_WATERMARK: bool = False
    DEFAULT_WATERMARK_POSITION: str = "top_right"  # "top_right", "bottom_right", "top_left", "bottom_left", "auto"
    DEFAULT_ENHANCE_QUALITY: bool = True
    DEFAULT_HOOK_STRATEGY: str = "teaser_climax_hook"  # "teaser_climax_hook", "direct_chronological"
    TARGET_WIDTH: int = 1080
    TARGET_HEIGHT: int = 1920




    # Scoring Weights (from GEMINI.md)
    SCORING_WEIGHTS: Dict[str, float] = Field(default_factory=lambda: {
        "hook": 0.18,
        "retention": 0.18,
        "emotion": 0.12,
        "story": 0.12,
        "payoff": 0.12,
        "curiosity": 0.10,
        "shareability": 0.08,
        "novelty": 0.04,
        "quotability": 0.04,
        "visual": 0.01,
        "audio": 0.01,
    })

    def ensure_directories(self) -> None:
        """Create data directories if they do not exist."""
        for path in [
            self.DATA_DIR,
            self.UPLOAD_DIR,
            self.PROCESSED_DIR,
            self.THUMBNAIL_DIR,
            self.SUBTITLE_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
