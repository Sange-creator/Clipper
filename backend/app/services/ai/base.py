"""Abstract Base Class for AI Reasoning Providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RawCandidateMoment(BaseModel):
    """Initial candidate moment identified from content."""
    start: float
    end: float
    hook_score: float = Field(default=80.0, ge=0.0, le=100.0)
    retention_score: float = Field(default=80.0, ge=0.0, le=100.0)
    curiosity_score: float = Field(default=80.0, ge=0.0, le=100.0)
    emotion_score: float = Field(default=80.0, ge=0.0, le=100.0)
    story_score: float = Field(default=80.0, ge=0.0, le=100.0)
    payoff_score: float = Field(default=80.0, ge=0.0, le=100.0)
    shareability_score: float = Field(default=80.0, ge=0.0, le=100.0)
    novelty_score: float = Field(default=80.0, ge=0.0, le=100.0)
    quotability_score: float = Field(default=80.0, ge=0.0, le=100.0)
    standalone_score: float = Field(default=80.0, ge=0.0, le=100.0)
    rewatch_score: float = Field(default=75.0, ge=0.0, le=100.0)
    visual_score: float = Field(default=75.0, ge=0.0, le=100.0)
    audio_score: float = Field(default=80.0, ge=0.0, le=100.0)
    platform_score: float = Field(default=80.0, ge=0.0, le=100.0)
    reason: str = ""
    hook_summary: str = ""
    payoff_summary: str = ""
    climax_start: Optional[float] = None  # Start timestamp of 4-5s peak clash/fight/shock
    climax_end: Optional[float] = None    # End timestamp of 4-5s peak clash/fight/shock
    climax_summary: Optional[str] = None  # Brief summary of peak shock moment


class ContentAnalysisResult(BaseModel):
    """Overall summary and structural breakdown of the source video."""
    summary: str
    main_topics: List[str] = []
    tone: str = ""
    key_themes: List[str] = []


class PlatformClipMetadata(BaseModel):
    """Platform-optimized titles, descriptions, and hashtags."""
    tiktok_title: str
    tiktok_caption: str
    tiktok_hashtags: List[str]
    reels_caption: str
    reels_hashtags: List[str]
    shorts_title: str
    shorts_description: str
    shorts_hashtags: List[str]


class AIProvider(ABC):
    """Abstract interface for AI reasoning engines."""

    @abstractmethod
    async def analyze_content(self, transcript: str, media_info: Dict[str, Any]) -> ContentAnalysisResult:
        """Analyze overall context, topics, and tone of the video."""
        pass

    @abstractmethod
    async def generate_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        requested_count: int,
        duration_target: str = "30-45s",
        mode: str = "podcast",
        custom_instructions: Optional[str] = None,
    ) -> List[RawCandidateMoment]:
        """Discover an oversized pool of candidate moments (e.g. 5x-10x requested count)."""
        pass

    @abstractmethod
    async def rank_candidates(
        self,
        candidates: List[RawCandidateMoment],
        transcript_context: str,
    ) -> List[RawCandidateMoment]:
        """Re-rank candidate pool with deep contextual evaluation."""
        pass

    @abstractmethod
    async def generate_metadata(
        self,
        clip_transcript: str,
        clip_context: Dict[str, Any],
    ) -> PlatformClipMetadata:
        """Generate platform-specific titles, captions, and hashtags for TikTok, Reels, Shorts."""
        pass

    @abstractmethod
    async def analyze_visual_context(self, frame_paths: List[str]) -> Dict[str, Any]:
        """Analyze key visual frames for visual engagement and activity."""
        pass
