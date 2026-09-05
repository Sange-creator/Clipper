"""Groq AI reasoning provider utilizing fast open-source models with structured output."""

import json
import logging
from typing import Any, Dict, List, Optional
from groq import AsyncGroq
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

import re

logger = logging.getLogger(__name__)


def clean_json_text(text: str) -> str:
    """Strip reasoning/think tags and markdown code fence blocks if present."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


class GroqProvider(AIProvider):
    """Groq fast AI Reasoning Engine for candidate discovery and metadata generation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL or "openai/gpt-oss-120b"
        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            self.client = None

    async def analyze_content(self, transcript: str, media_info: Dict[str, Any]) -> ContentAnalysisResult:
        if not self.client:
            raise AIProviderError("Groq API key is not configured.")

        prompt = f"""Analyze this transcript and return JSON with keys summary, main_topics, tone, key_themes:
{transcript[:6000]}"""
        try:
            chat = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert video content analyst. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            raw = clean_json_text(chat.choices[0].message.content or "{}")
            data = json.loads(raw)
            return ContentAnalysisResult(**data)
        except Exception as e:
            logger.warning(f"Groq content analysis fallback: {e}")
            return ContentAnalysisResult(
                summary="Content analysis summary",
                main_topics=["Video Content"],
                tone="Informative",
                key_themes=["Highlights"],
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
        if not self.client:
            raise AIProviderError("Groq API key is not configured.")

        pool_size = max(requested_count * 5, 40)
        v_title = media_info.get("video_title") or media_info.get("filename") or "Video Highlights"
        v_genre = media_info.get("genre") or mode or "viral_moments"
        system_instruction = get_discovery_prompt(
            mode=mode,
            duration_target=duration_target,
            pool_size=pool_size,
            video_title=v_title,
            genre=v_genre,
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
Return JSON with key 'candidates' containing a list of candidate moment objects:
{custom_note}

Transcript:
{transcript_body}
"""

        try:
            chat = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction + "\nReturn ONLY valid JSON."},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
            )
            raw = clean_json_text(chat.choices[0].message.content or "{}")
            data = json.loads(raw)
            raw_list = data.get("candidates", []) if isinstance(data, dict) else data

            candidates: List[RawCandidateMoment] = []
            for item in raw_list:
                try:
                    candidates.append(RawCandidateMoment(**item))
                except ValidationError:
                    continue
            return candidates
        except Exception as e:
            logger.error(f"Groq candidate generation error: {e}")
            raise AIProviderError(f"Groq candidate discovery failed: {e}")

    async def rank_candidates(
        self,
        candidates: List[RawCandidateMoment],
        requested_count: int,
    ) -> List[RawCandidateMoment]:
        return sorted(
            candidates,
            key=lambda c: (c.hook_score * 0.4 + c.retention_score * 0.4 + c.payoff_score * 0.2),
            reverse=True,
        )[:requested_count]

    async def generate_metadata(
        self,
        clip_transcript: str,
        video_context: Dict[str, Any],
    ) -> PlatformClipMetadata:
        if not self.client:
            raise AIProviderError("Groq API key is not configured.")

        part_idx = video_context.get("part_index")
        total_p = video_context.get("total_parts")
        series_line = f"\nSeries Info: Part {part_idx} of {total_p}" if part_idx and total_p else ""
        source_title = video_context.get("video_title", "")
        title_line = f"\nSource Video Title: {source_title}" if source_title else ""

        user_prompt = f"""Generate platform metadata for this clip transcript:
"{clip_transcript}"

Context:
Hook Summary: {video_context.get('hook_summary', '') or video_context.get('summary', '')}
Payoff Summary: {video_context.get('payoff_summary', '')}{title_line}{series_line}
"""
        try:
            chat = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": METADATA_SYSTEM_PROMPT + "\nReturn ONLY valid JSON."},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
            )
            raw = clean_json_text(chat.choices[0].message.content or "{}")
            data = json.loads(raw)

            if not data.get("single_para_copy"):
                tt_t = data.get("tiktok_title", "Viral Clip")
                tt_c = data.get("tiktok_caption", "")
                tags_str = " ".join(data.get("tiktok_hashtags", ["#fyp", "#viral", "#shorts"]))
                data["single_para_copy"] = f"{tt_t} — {tt_c} {tags_str}".strip()

            data["part_index"] = part_idx
            data["total_parts"] = total_p
            return PlatformClipMetadata(**data)
        except Exception as e:
            logger.warning(f"Groq metadata generation fallback: {e}")
            hook_lead = video_context.get("hook_summary", "").strip() or video_context.get("summary", "").strip() or " ".join(clip_transcript.split()[:7])
            title = hook_lead if len(hook_lead) > 8 else "Wait until you see how this ends..."
            title = title.rstrip(".!?")
            if part_idx and total_p:
                title = f"PART {part_idx}/{total_p}: {title}"
            tags = ["#fyp", "#viral", "#foryou", "#truth", "#trending"]
            caption = f"{title}. Nobody talks about this part. Thoughts? 👇"
            if part_idx and total_p and part_idx < total_p:
                caption += f" Follow for Part {part_idx + 1}!"
            single_para = f"{title} — {caption} {' '.join(tags)}"
            return PlatformClipMetadata(
                tiktok_title=f"{title[:50]}",
                tiktok_caption=caption,
                tiktok_hashtags=tags,
                reels_caption=f"{title}\n\nThe part everyone completely missed.\n\n📌 Save this for later | 📲 Share with someone who needs this\n\n{' '.join(tags)}",
                reels_hashtags=["#reels", "#explorepage", "#viralreels", "#mindset", "#shorts"],
                shorts_title=f"{title[:45]} #shorts",
                shorts_description=f"{clip_transcript[:200]}...\n\nSubscribe for daily clips!\n\n{' '.join(tags)}",
                shorts_hashtags=["#shorts", "#viral", "#trending"],
                single_para_copy=single_para,
                part_index=part_idx,
                total_parts=total_p,
            )


    async def analyze_visual_context(
        self,
        frame_paths: List[str],
        timestamp: float,
    ) -> Dict[str, Any]:
        return {
            "timestamp": timestamp,
            "visual_interest_score": 75.0,
            "detected_subjects": ["speaker"],
            "framing_recommendation": "center_single",
        }
