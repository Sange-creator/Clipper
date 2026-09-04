"""SQLAlchemy ORM models for the AI Video Clipper platform (Next Version)."""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def generate_uuid() -> str:
    """Generate a clean hex UUID string."""
    return uuid.uuid4().hex


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base ORM class."""
    pass


class Project(Base):
    """Represents a multi-video project workspace containing 20-30+ source videos."""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255))
    mode: Mapped[str] = mapped_column(String(32), default="podcast")  # "podcast" | "viral_moments"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    settings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="project", cascade="all, delete-orphan")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="project", cascade="all, delete-orphan")


class Video(Base):
    """Represents an uploaded source video."""
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    fps: Mapped[float] = mapped_column(Float, default=0.0)
    video_codec: Mapped[str] = mapped_column(String(64), default="")
    audio_codec: Mapped[str] = mapped_column(String(64), default="")
    bitrate: Mapped[int] = mapped_column(BigInteger, default=0)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="videos")
    transcripts: Mapped[List["Transcript"]] = relationship("Transcript", back_populates="video", cascade="all, delete-orphan")
    scenes: Mapped[List["Scene"]] = relationship("Scene", back_populates="video", cascade="all, delete-orphan")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="video", cascade="all, delete-orphan")


class Transcript(Base):
    """Represents a timestamped speech-to-text transcript."""
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    language: Mapped[str] = mapped_column(String(16), default="en")
    full_text: Mapped[str] = mapped_column(Text)
    segments_json: Mapped[str] = mapped_column(Text)  # Detailed segment & word timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationship
    video: Mapped["Video"] = relationship("Video", back_populates="transcripts")


class Scene(Base):
    """Represents a detected visual scene cut."""
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    scene_index: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    keyframe_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    video: Mapped["Video"] = relationship("Video", back_populates="scenes")


class Job(Base):
    """Represents a 21-stage clipping processing pipeline job with checkpointing."""
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    video_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(32), default="podcast")  # "podcast" | "viral_moments"
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)  # queued, processing, completed, failed, cancelled
    current_stage: Mapped[int] = mapped_column(Integer, default=1)
    stage_name: Mapped[str] = mapped_column(String(64), default="Validate file")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    burn_captions: Mapped[bool] = mapped_column(Boolean, default=True)
    remove_dead_air: Mapped[bool] = mapped_column(Boolean, default=True)
    framing_mode: Mapped[str] = mapped_column(String(32), default="crop_9_16")  # "crop_9_16", "blur_fit_9_16", "original_16_9"
    blur_radius: Mapped[int] = mapped_column(Integer, default=30)  # 10..80
    subtitle_position: Mapped[int] = mapped_column(Integer, default=75)  # 10..90 percent from top
    add_hook_header: Mapped[bool] = mapped_column(Boolean, default=False)  # Sticky TikTok hook header
    hook_header_position: Mapped[int] = mapped_column(Integer, default=12)  # 8..90 percent from top
    hook_header_style: Mapped[str] = mapped_column(String(64), default="viral_creator")  # viral_creator, white_box, meme, nostalgic, old_history, neon_cyber
    remove_watermark: Mapped[bool] = mapped_column(Boolean, default=False)  # Delogo / erase watermark
    watermark_position: Mapped[str] = mapped_column(String(32), default="top_right")  # "top_right", "bottom_right", "top_left", "bottom_left", "tiktok_bounce", "all_corners", "auto"
    enhance_quality: Mapped[bool] = mapped_column(Boolean, default=True)  # Studio color & detail boost
    hook_strategy: Mapped[str] = mapped_column(String(32), default="teaser_climax_hook")  # "teaser_climax_hook" | "direct_chronological"
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)



    log_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stage_checkpoint_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Checkpointed stage artifacts for resumption
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="jobs")
    video: Mapped[Optional["Video"]] = relationship("Video", back_populates="jobs")
    candidates: Mapped[List["ClipCandidate"]] = relationship("ClipCandidate", back_populates="job", cascade="all, delete-orphan")
    rendered_clips: Mapped[List["RenderedClip"]] = relationship("RenderedClip", back_populates="job", cascade="all, delete-orphan")


class ClipCandidate(Base):
    """Represents a high-potential clip candidate moment scored across 12 dimensions."""
    __tablename__ = "clip_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)
    
    # 12-Dimensional normalized 0-100 scores
    hook_score: Mapped[float] = mapped_column(Float, default=0.0)
    retention_score: Mapped[float] = mapped_column(Float, default=0.0)
    curiosity_score: Mapped[float] = mapped_column(Float, default=0.0)
    emotion_score: Mapped[float] = mapped_column(Float, default=0.0)
    story_score: Mapped[float] = mapped_column(Float, default=0.0)
    payoff_score: Mapped[float] = mapped_column(Float, default=0.0)
    shareability_score: Mapped[float] = mapped_column(Float, default=0.0)
    novelty_score: Mapped[float] = mapped_column(Float, default=0.0)
    quotability_score: Mapped[float] = mapped_column(Float, default=0.0)
    standalone_score: Mapped[float] = mapped_column(Float, default=0.0)
    rewatch_score: Mapped[float] = mapped_column(Float, default=0.0)
    visual_score: Mapped[float] = mapped_column(Float, default=0.0)
    audio_score: Mapped[float] = mapped_column(Float, default=0.0)
    platform_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    composite_score: Mapped[float] = mapped_column(Float, default=0.0)
    penalty_deduction: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    
    hook_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payoff_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timeline_edit_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Kept interval slices
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="candidates")
    rendered_clip: Mapped[Optional["RenderedClip"]] = relationship("RenderedClip", back_populates="candidate", uselist=False)


class RenderedClip(Base):
    """Represents a rendered 9:16 vertical short clip with burned captions and platform metadata."""
    __tablename__ = "rendered_clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("clip_candidates.id", ondelete="CASCADE"), unique=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(32), default="podcast")  # "podcast" | "viral_moments"
    
    video_path: Mapped[str] = mapped_column(Text)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    srt_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ass_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)
    aspect_ratio: Mapped[str] = mapped_column(String(16), default="9:16")
    framing_mode: Mapped[str] = mapped_column(String(32), default="crop_9_16")  # "crop_9_16", "blur_fit_9_16", "original_16_9"
    blur_radius: Mapped[int] = mapped_column(Integer, default=30)  # 10..80
    subtitle_position: Mapped[int] = mapped_column(Integer, default=75)  # 10..90 percent from top
    add_hook_header: Mapped[bool] = mapped_column(Boolean, default=False)  # Sticky TikTok hook header
    hook_header_position: Mapped[int] = mapped_column(Integer, default=12)  # 8..90 percent from top
    hook_header_style: Mapped[str] = mapped_column(String(64), default="viral_creator")
    hook_header_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remove_watermark: Mapped[bool] = mapped_column(Boolean, default=False)  # Delogo / erase watermark
    watermark_position: Mapped[str] = mapped_column(String(32), default="top_right")  # "top_right", "bottom_right", "top_left", "bottom_left"
    enhance_quality: Mapped[bool] = mapped_column(Boolean, default=True)  # Studio color & detail boost
    hook_strategy: Mapped[str] = mapped_column(String(32), default="teaser_climax_hook")  # "teaser_climax_hook" | "direct_chronological"
    caption_style: Mapped[str] = mapped_column(String(32), default="bold_yellow")

    burn_captions: Mapped[bool] = mapped_column(Boolean, default=True)
    timeline_edit_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    
    # Platform-specific optimization
    tiktok_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tiktok_caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tiktok_hashtags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    reels_caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reels_hashtags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    shorts_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shorts_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shorts_hashtags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    candidate: Mapped["ClipCandidate"] = relationship("ClipCandidate", back_populates="rendered_clip")
    job: Mapped["Job"] = relationship("Job", back_populates="rendered_clips")
    feedbacks: Mapped[List["UserFeedback"]] = relationship("UserFeedback", back_populates="clip", cascade="all, delete-orphan")
    analytics: Mapped[List["PerformanceAnalytics"]] = relationship("PerformanceAnalytics", back_populates="clip", cascade="all, delete-orphan")


class UserFeedback(Base):
    """Tracks human review actions and feedback for future quality learning."""
    __tablename__ = "user_feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    clip_id: Mapped[str] = mapped_column(String(36), ForeignKey("rendered_clips.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(32))  # accepted, rejected, favorite, manually_edited, regenerated
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    clip: Mapped["RenderedClip"] = relationship("RenderedClip", back_populates="feedbacks")


class AIRequestLog(Base):
    """Audit trail and observability log for external and local AI requests."""
    __tablename__ = "ai_request_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    provider: Mapped[str] = mapped_column(String(32))  # gemini, groq, mock
    model: Mapped[str] = mapped_column(String(64))
    stage: Mapped[str] = mapped_column(String(64))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="success")  # success, error, fallback
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class PerformanceAnalytics(Base):
    """Schema for future learning system to track historical clip performance."""
    __tablename__ = "performance_analytics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    clip_id: Mapped[str] = mapped_column(String(36), ForeignKey("rendered_clips.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(32))  # tiktok, reels, shorts
    views: Mapped[int] = mapped_column(Integer, default=0)
    watch_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    clip: Mapped["RenderedClip"] = relationship("RenderedClip", back_populates="analytics")


class SystemSetting(Base):
    """Dynamic system and API settings persisted in database."""
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

