"""Mock / Heuristic AI provider for deterministic testing and offline operation."""

import re
from typing import Any, Dict, List, Optional
from app.services.ai.base import (
    AIProvider,
    ContentAnalysisResult,
    PlatformClipMetadata,
    RawCandidateMoment,
)

HOOK_KEYWORDS = [
    "insane", "crazy", "chaotic", "unbelievable", "wtf", "screaming", "fight",
    "shut up", "lie", "ruined", "disaster", "warning", "never do this", "banned",
    "illegal", "expose", "secret", "worst mistake", "scam", "crying", "shocking",
    "panic", "plot twist", "caught", "destroyed", "stop", "never", "why", "how",
    "what if", "nobody tells you", "actually", "listen", "look"
]

CHAOTIC_HOOKS = [
    "Wait until you see how this ends...",
    "This is the most insane thing I've ever heard 😳",
    "Nobody knows this secret, but it changes everything",
    "Stop doing this immediately or you will lose everything 🚨",
    "I was not expecting this to happen at all...",
    "This completely exposed the whole truth 🤯",
    "The biggest mistake everyone is making right now",
    "Watch what happens when he realized the truth...",
    "This is pure chaos and nobody is talking about it",
    "I still can't believe they actually said this on camera",
]

PAYOFF_KEYWORDS = [
    "so that's why", "in conclusion", "the result", "finally", "remember",
    "bottom line", "lesson", "takeaway", "and that changed everything",
    "which means", "the truth is", "that is how", "payoff"
]


from app.services.media.audio_analyzer import audio_hook_analyzer


class MockAIProvider(AIProvider):
    """Linguistic & Acoustic AI provider that analyzes real spoken dialogue deterministically."""

    async def analyze_content(self, transcript: str, media_info: Dict[str, Any]) -> ContentAnalysisResult:
        words = transcript.split()
        summary = " ".join(words[:40]) + ("..." if len(words) > 40 else "")
        return ContentAnalysisResult(
            summary=f"Analysis of {len(words)} word source video: {summary}",
            main_topics=["Key Insights", "Storytelling", "Actionable Takeaways"],
            tone="Engaging & Insightful",
            key_themes=["High Retention", "Viral Hooks", "Climax"],
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
        if not transcript_segments:
            duration = media_info.get("duration_seconds", 60.0)
            return [
                RawCandidateMoment(
                    start=0.0,
                    end=min(30.0, duration),
                    hook_score=85.0,
                    retention_score=82.0,
                    curiosity_score=88.0,
                    emotion_score=80.0,
                    story_score=85.0,
                    payoff_score=84.0,
                    shareability_score=80.0,
                    novelty_score=78.0,
                    quotability_score=80.0,
                    standalone_score=85.0,
                    rewatch_score=78.0,
                    visual_score=80.0,
                    audio_score=85.0,
                    platform_score=85.0,
                    reason=f"Engaging sequence from source video.",
                    hook_summary="Opening hook",
                    payoff_summary="Resolution moment",
                )
            ]

        # Analyze authentic spoken dialogue with AudioHookAnalyzer
        candidates = audio_hook_analyzer.discover_candidates(
            transcript_segments=transcript_segments,
            media_info=media_info,
            requested_count=requested_count,
            duration_target=duration_target,
            mode=mode,
        )

        if not candidates:
            # Fallback across video duration if no candidate matched thresholds
            total_dur = float(media_info.get("duration_seconds") or 60.0)
            first_text = transcript_segments[0].get("text", "Engaging opening")[:60]
            candidates.append(
                RawCandidateMoment(
                    start=0.0,
                    end=min(30.0, total_dur),
                    hook_score=88.0,
                    retention_score=86.0,
                    curiosity_score=88.0,
                    emotion_score=82.0,
                    story_score=85.0,
                    payoff_score=84.0,
                    shareability_score=82.0,
                    novelty_score=80.0,
                    quotability_score=82.0,
                    standalone_score=85.0,
                    rewatch_score=80.0,
                    visual_score=82.0,
                    audio_score=86.0,
                    platform_score=88.0,
                    reason=f"High-retention opening segment: '{first_text}'",
                    hook_summary=first_text,
                    payoff_summary="Resolution moment",
                )
            )

        return candidates

    async def rank_candidates(
        self,
        candidates: List[RawCandidateMoment],
        transcript_context: str,
    ) -> List[RawCandidateMoment]:
        # Rank by hook velocity and audience retention
        return sorted(
            candidates,
            key=lambda c: (c.hook_score * 0.40 + c.retention_score * 0.35 + c.payoff_score * 0.25),
            reverse=True,
        )

    async def generate_metadata(
        self,
        clip_transcript: str,
        clip_context: Dict[str, Any],
    ) -> PlatformClipMetadata:
        hook = clip_context.get("hook_summary", "")
        payoff = clip_context.get("payoff_summary", "")
        part_idx = clip_context.get("part_index")
        total_p = clip_context.get("total_parts")
        v_title = clip_context.get("video_title")
        return audio_hook_analyzer.generate_clip_metadata(
            clip_transcript=clip_transcript,
            hook_summary=hook,
            payoff_summary=payoff,
            part_index=part_idx,
            total_parts=total_p,
            video_title=v_title,
        )

    async def analyze_visual_context(self, frame_paths: List[str]) -> Dict[str, Any]:
        return {"visual_engagement": 84.0, "face_detected": True}

