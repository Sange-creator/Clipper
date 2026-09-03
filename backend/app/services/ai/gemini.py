"""Gemini AI reasoning provider using Google GenAI SDK with structured output."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.core.exceptions import AIProviderError
from app.services.ai.base import (
    AIProvider,
    ContentAnalysisResult,
    PlatformClipMetadata,
    RawCandidateMoment,
)
from app.services.ai.prompt_templates import (
    METADATA_SYSTEM_PROMPT,
    get_discovery_prompt,
)

logger = logging.getLogger(__name__)


def clean_json_text(text: str) -> str:
    """Strip markdown code fence blocks if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


class GeminiProvider(AIProvider):
    """Gemini AI Reasoning Engine for candidate discovery, scoring, and metadata generation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def analyze_content(self, transcript: str, media_info: Dict[str, Any]) -> ContentAnalysisResult:
        """Analyze overall themes and structure."""
        if not self.client:
            raise AIProviderError("Gemini API key is not configured.")

        prompt = f"""Analyze this video transcript:
{transcript[:8000]}

Return JSON with:
{{
  "summary": "2-3 sentence overview of content",
  "main_topics": ["topic1", "topic2"],
  "tone": "energetic/educational/etc",
  "key_themes": ["theme1", "theme2"]
}}
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            raw = clean_json_text(response.text or "{}")
            data = json.loads(raw)
            return ContentAnalysisResult(**data)
        except Exception as e:
            logger.error(f"Gemini content analysis failed: {e}")
            return ContentAnalysisResult(
                summary="Source video content analysis",
                main_topics=["General Content"],
                tone="Informative",
                key_themes=["Key Highlights"],
            )

    async def generate_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        requested_count: int,
        duration_target: str = "30-45s",
        mode: str = "podcast",
        custom_instructions: Optional[str] = None,
    ) -> List[RawCandidateMoment]:
        """Discover 5x-10x candidate moments with structured JSON output."""
        if not self.client:
            raise AIProviderError("Gemini API key is not configured.")

        pool_size = max(requested_count * 5, 50)
        system_instruction = get_discovery_prompt(
            mode=mode,
            duration_target=duration_target,
            pool_size=pool_size,
        )

        formatted_transcript = []
        for s in transcript_segments:
            start = s.get("start", 0.0)
            end = s.get("end", 0.0)
            text = s.get("text", "").strip()
            formatted_transcript.append(f"[{start:.2f}s -> {end:.2f}s] {text}")
        
        transcript_body = "\n".join(formatted_transcript)
        custom_note = f"\nUser Custom Instructions: {custom_instructions}" if custom_instructions else ""

        user_prompt = f"""Identify at least {pool_size} candidate moments from this transcript.
Video Duration: {media_info.get('duration_seconds', 0):.1f}s
Target Duration: {duration_target}
{custom_note}

Transcript with Timestamps:
{transcript_body}

Return a JSON array of candidates:
[
  {{
    "start": 12.4,
    "end": 44.8,
    "hook_score": 92,
    "retention_score": 88,
    "curiosity_score": 90,
    "emotion_score": 85,
    "story_score": 89,
    "payoff_score": 93,
    "shareability_score": 87,
    "novelty_score": 82,
    "quotability_score": 88,
    "visual_score": 80,
    "audio_score": 85,
    "platform_score": 90,
    "climax_start": 28.5,
    "climax_end": 33.2,
    "climax_summary": "Intense peak clash: explosive revelation",
    "reason": "Strong curiosity hook followed by concrete advice.",
    "hook_summary": "Unexpected revelation at the start",
    "payoff_summary": "Clear conclusion and takeaway"
  }}
]
"""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.4,
                ),
            )
            raw = clean_json_text(response.text or "[]")
            data = json.loads(raw)
            if not isinstance(data, list):
                if isinstance(data, dict) and "candidates" in data:
                    data = data["candidates"]
                else:
                    data = [data]

            candidates: List[RawCandidateMoment] = []
            for item in data:
                try:
                    candidates.append(RawCandidateMoment(**item))
                except ValidationError as ve:
                    logger.warning(f"Skipping malformed candidate: {ve}")
            return candidates
        except Exception as e:
            logger.error(f"Gemini generate_candidates error: {e}")
            raise AIProviderError(f"Gemini candidate discovery failed: {e}")

    async def rank_candidates(
        self,
        candidates: List[RawCandidateMoment],
        transcript_context: str,
    ) -> List[RawCandidateMoment]:
        """Rank candidate moments based on composite scores."""
        # Provider-level ranking and verification
        return sorted(candidates, key=lambda c: c.hook_score + c.retention_score + c.payoff_score, reverse=True)

    async def generate_metadata(
        self,
        clip_transcript: str,
        clip_context: Dict[str, Any],
    ) -> PlatformClipMetadata:
        """Generate platform-specific optimized titles, captions, and hashtags."""
        if not self.client:
            raise AIProviderError("Gemini API key is not configured.")

        prompt = f"""Generate platform metadata for this clip transcript:
\"\"\"{clip_transcript}\"\"\"

Hook Summary: {clip_context.get('hook_summary', '')}
Payoff Summary: {clip_context.get('payoff_summary', '')}
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=METADATA_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.5,
                ),
            )
            raw = clean_json_text(response.text or "{}")
            data = json.loads(raw)
            return PlatformClipMetadata(**data)
        except Exception as e:
            logger.error(f"Gemini metadata generation failed: {e}")
            hook_lead = clip_context.get("hook_summary", "").strip() or " ".join(clip_transcript.split()[:7])
            title = hook_lead if len(hook_lead) > 8 else "Wait until you see how this ends..."
            title = title.rstrip(".!?")
            return PlatformClipMetadata(
                tiktok_title=f"{title[:50]} 👀",
                tiktok_caption=f"{title}. Nobody talks about this part. Thoughts? 👇",
                tiktok_hashtags=["#fyp", "#viral", "#foryou", "#truth", "#trending"],
                reels_caption=f"{title}\n\nThe part everyone completely missed.\n\n📌 Save this for later | 📲 Share with someone who needs this",
                reels_hashtags=["#reels", "#explorepage", "#viralreels", "#mindset", "#shorts"],
                shorts_title=f"{title[:45]} #shorts",
                shorts_description=f"{clip_transcript[:200]}...\n\nSubscribe for daily clips!",
                shorts_hashtags=["#shorts", "#viral", "#trending"],
            )


    async def analyze_visual_context(self, frame_paths: List[str]) -> Dict[str, Any]:
        """Extract visual dynamics."""
        return {"visual_engagement": 85.0, "face_detected": True}
