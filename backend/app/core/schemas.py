"""Pydantic v2 schemas for request validation and response serialization (Next Version)."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# Video schemas
class VideoInfo(BaseModel):
    id: str
    project_id: Optional[str] = None
    filename: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str
    file_size_bytes: int
    created_at: datetime
    video_url: Optional[str] = None


class VideoUploadResponse(BaseModel):
    video: VideoInfo
    is_duplicate: bool = False
    message: str = "Video uploaded and inspected successfully."


class BatchUploadResponse(BaseModel):
    uploaded_videos: List[VideoInfo]
    duplicates_count: int = 0
    failed_count: int = 0
    total_processed: int = 0
    message: str = "Batch upload completed successfully."


# Project schemas
class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    default_caption_style: Optional[str] = "bold_yellow"
    default_duration_preset: Optional[str] = "30-45s"


class ProjectListItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    video_count: int = 0
    clips_count: int = 0
    created_at: datetime
    updated_at: datetime


# Platform Metadata schemas
class PlatformMetadata(BaseModel):
    tiktok_title: str = ""
    tiktok_caption: str = ""
    tiktok_hashtags: List[str] = []
    reels_caption: str = ""
    reels_hashtags: List[str] = []
    shorts_title: str = ""
    shorts_description: str = ""
    shorts_hashtags: List[str] = []


# Candidate & Score schemas
class CandidateScores(BaseModel):
    hook_score: float = 0.0
    retention_score: float = 0.0
    curiosity_score: float = 0.0
    emotion_score: float = 0.0
    story_score: float = 0.0
    payoff_score: float = 0.0
    shareability_score: float = 0.0
    novelty_score: float = 0.0
    quotability_score: float = 0.0
    standalone_score: float = 0.0
    rewatch_score: float = 0.0
    visual_score: float = 0.0
    audio_score: float = 0.0
    platform_score: float = 0.0
    composite_score: float = 0.0
    penalty_deduction: float = 0.0


class CandidateDetail(BaseModel):
    id: str
    job_id: str
    video_id: str
    start_time: float
    end_time: float
    duration: float
    scores: CandidateScores
    rank: int
    selected: bool
    hook_text: Optional[str] = None
    payoff_text: Optional[str] = None
    transcript_text: Optional[str] = None
    timeline_edit: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


# Rendered Clip schemas
class RenderedClipResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    video_id: str
    mode: str = "podcast"
    video_url: str
    thumbnail_url: Optional[str] = None
    srt_url: Optional[str] = None
    ass_url: Optional[str] = None
    start_time: float
    end_time: float
    duration: float
    aspect_ratio: str = "9:16"
    framing_mode: str = "crop_9_16"
    blur_radius: int = 30
    subtitle_position: int = 75
    add_hook_header: bool = False
    hook_header_position: int = 12
    hook_header_text: Optional[str] = None
    remove_watermark: bool = False
    watermark_position: str = "top_right"
    enhance_quality: bool = True
    caption_style: str = "bold_yellow"
    burn_captions: bool = True
    timeline_edit: Optional[Dict[str, Any]] = None
    scores: CandidateScores
    reason: Optional[str] = None
    hook_text: Optional[str] = None
    payoff_text: Optional[str] = None
    metadata: PlatformMetadata
    is_favorite: bool = False
    is_rejected: bool = False
    created_at: datetime


class ProjectCreateRequest(BaseModel):
    name: str
    mode: Literal["podcast", "viral_moments"] = "podcast"
    description: Optional[str] = None


class ProjectListItem(BaseModel):
    id: str
    name: str
    mode: str = "podcast"
    description: Optional[str] = None
    video_count: int = 0
    clips_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(BaseModel):
    id: str
    name: str
    mode: str = "podcast"
    description: Optional[str] = None
    videos: List[VideoInfo] = []
    clips: List[RenderedClipResponse] = []
    total_videos: int = 0
    total_clips: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectProcessRequest(BaseModel):
    mode: Optional[Literal["podcast", "viral_moments"]] = None
    target_clips_count: int = Field(default=20, ge=1, le=100)
    duration_preset: Literal["15-30s", "30-45s", "45-60s", "60-90s", "custom"] = "30-45s"
    caption_style: str = "bold_yellow"
    burn_captions: bool = True
    remove_dead_air: bool = True
    framing_mode: Literal["crop_9_16", "blur_fit_9_16", "original_16_9"] = "crop_9_16"
    blur_radius: int = Field(default=30, ge=5, le=100)
    subtitle_position: int = Field(default=75, ge=10, le=90)
    add_hook_header: bool = False
    hook_header_position: int = Field(default=12, ge=8, le=90)
    remove_watermark: bool = False
    watermark_position: Literal["top_right", "bottom_right", "top_left", "bottom_left"] = "top_right"
    enhance_quality: bool = True
    reframing_mode: Literal["smart_face_track", "center_crop"] = "center_crop"
    ai_provider: Optional[Literal["gemini", "groq", "mock"]] = None
    source_diversity_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    custom_instructions: Optional[str] = None


# Job schemas
class JobCreateRequest(BaseModel):
    video_id: Optional[str] = None
    project_id: Optional[str] = None
    mode: Literal["podcast", "viral_moments"] = "podcast"
    target_clips_count: int = Field(default=10, ge=1, le=50)
    duration_preset: Literal["15-30s", "30-45s", "45-60s", "60-90s", "custom"] = "30-45s"
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    ai_provider: Optional[Literal["gemini", "groq", "mock"]] = None
    caption_style: str = "bold_yellow"
    burn_captions: bool = True
    remove_dead_air: bool = True
    framing_mode: Literal["crop_9_16", "blur_fit_9_16", "original_16_9"] = "crop_9_16"
    blur_radius: int = Field(default=30, ge=5, le=100)
    subtitle_position: int = Field(default=75, ge=10, le=90)
    add_hook_header: bool = False
    hook_header_position: int = Field(default=12, ge=8, le=90)
    remove_watermark: bool = False
    watermark_position: Literal["top_right", "bottom_right", "top_left", "bottom_left"] = "top_right"
    enhance_quality: bool = True
    reframing_mode: Literal["smart_face_track", "center_crop"] = "center_crop"
    custom_instructions: Optional[str] = None


class JobStatusResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    video_id: Optional[str] = None
    mode: str = "podcast"
    status: str
    current_stage: int
    stage_name: str
    progress: float
    total_candidates_found: int = 0
    total_clips_rendered: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    logs: List[Dict[str, Any]] = []


class ClipEditRequest(BaseModel):
    start_time: float
    end_time: float
    caption_style: Optional[str] = None
    burn_captions: bool = True
    remove_dead_air: bool = True
    framing_mode: Optional[Literal["crop_9_16", "blur_fit_9_16", "original_16_9"]] = None
    blur_radius: Optional[int] = Field(default=None, ge=5, le=100)
    subtitle_position: Optional[int] = Field(default=None, ge=10, le=90)
    add_hook_header: Optional[bool] = None
    hook_header_position: Optional[int] = Field(default=None, ge=8, le=90)
    hook_header_text: Optional[str] = None
    remove_watermark: Optional[bool] = None
    watermark_position: Optional[Literal["top_right", "bottom_right", "top_left", "bottom_left"]] = None
    enhance_quality: Optional[bool] = None


class ClipRegenerateRequest(BaseModel):
    intent: Literal["stronger_hook", "shorter_duration", "longer_context", "different_payoff", "style_change"]
    caption_style: Optional[str] = None
    subtitle_position: Optional[int] = Field(default=None, ge=10, le=90)
    add_hook_header: Optional[bool] = None
    hook_header_position: Optional[int] = Field(default=None, ge=8, le=90)
    hook_header_text: Optional[str] = None
    remove_watermark: Optional[bool] = None
    watermark_position: Optional[Literal["top_right", "bottom_right", "top_left", "bottom_left"]] = None
    enhance_quality: Optional[bool] = None
    custom_note: Optional[str] = None


class UserFeedbackCreate(BaseModel):
    action: Literal["accepted", "rejected", "favorite", "manually_edited", "regenerated"]
    feedback_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BulkClipActionRequest(BaseModel):
    clip_ids: List[str]
    action: Literal["apply_style", "render", "reject", "favorite", "delete"]
    caption_style: Optional[str] = None


class AdminMetricsResponse(BaseModel):
    total_projects: int = 0
    total_videos: int = 0
    total_clips_generated: int = 0
    total_jobs: int = 0
    active_jobs: int = 0
    failed_jobs: int = 0
    avg_processing_time_sec: float = 0.0
    acceptance_rate_pct: float = 0.0
    rejection_rate_pct: float = 0.0
    manual_edit_rate_pct: float = 0.0
    total_ai_requests: int = 0
    ai_provider_stats: Dict[str, Any] = {}
    storage_bytes_used: int = 0


# System Settings schemas
class SettingsResponse(BaseModel):
    ai_provider: str
    gemini_api_key_configured: bool
    gemini_api_key_masked: str
    gemini_model: str
    groq_api_key_configured: bool
    groq_api_key_masked: str
    groq_model: str
    deepgram_api_key_configured: bool = False
    deepgram_api_key_masked: str = ""
    deepgram_model: str = "nova-3"
    transcriber_provider: str = "auto"
    whisper_model_size: str
    default_framing_mode: str = "crop_9_16"
    default_blur_radius: int = 30
    default_subtitle_position: int = 75
    default_add_hook_header: bool = False
    default_hook_header_position: int = 12
    default_remove_watermark: bool = False
    default_watermark_position: str = "top_right"
    default_enhance_quality: bool = True
    ffmpeg_available: bool
    ffprobe_available: bool


class SettingsUpdateRequest(BaseModel):
    ai_provider: Optional[Literal["gemini", "groq", "mock"]] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    groq_api_key: Optional[str] = None
    groq_model: Optional[str] = None
    deepgram_api_key: Optional[str] = None
    deepgram_model: Optional[str] = None
    transcriber_provider: Optional[str] = None
    whisper_model_size: Optional[str] = None
    default_framing_mode: Optional[Literal["crop_9_16", "blur_fit_9_16", "original_16_9"]] = None
    default_blur_radius: Optional[int] = Field(default=None, ge=5, le=100)
    default_subtitle_position: Optional[int] = Field(default=None, ge=10, le=90)
    default_add_hook_header: Optional[bool] = None
    default_hook_header_position: Optional[int] = Field(default=None, ge=8, le=90)
    default_remove_watermark: Optional[bool] = None
    default_watermark_position: Optional[Literal["top_right", "bottom_right", "top_left", "bottom_left"]] = None
    default_enhance_quality: Optional[bool] = None




class TestApiKeyRequest(BaseModel):
    provider: Literal["gemini", "groq", "deepgram"]
    api_key: str
    model: Optional[str] = None


class TestApiKeyResponse(BaseModel):
    valid: bool
    message: str
    model_tested: str


