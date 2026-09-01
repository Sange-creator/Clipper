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
    "secret", "never", "always", "crazy", "truth", "insane", "mistake",
    "why", "how", "what if", "stop", "unbelievable", "huge", "shocking",
    "the reason", "don't", "nobody tells you", "actually", "listen", "look"
]

PAYOFF_KEYWORDS = [
    "so that's why", "in conclusion", "the result", "finally", "remember",
    "bottom line", "lesson", "takeaway", "and that changed everything",
    "which means", "the truth is", "that is how", "payoff"
]


class MockAIProvider(AIProvider):
    """Heuristic NLP engine that generates realistic candidate moments deterministically."""

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
            # Fallback if empty transcript
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
                    reason=f"Engaging {mode} sequence with natural pacing.",
                    hook_summary="Opening hook",
                    payoff_summary="Resolution moment",
                )
            ]

        # Parse target duration range
        target_min = 20.0
        target_max = 50.0
        if "15-30" in duration_target:
            target_min, target_max = 15.0, 32.0
        elif "30-45" in duration_target:
            target_min, target_max = 28.0, 48.0
        elif "45-60" in duration_target:
            target_min, target_max = 42.0, 62.0
        elif "60-90" in duration_target:
            target_min, target_max = 58.0, 95.0

        candidates: List[RawCandidateMoment] = []
        num_segments = len(transcript_segments)

        # Sliding context window generation over transcript segments
        for i in range(num_segments):
            start_seg = transcript_segments[i]
            start_time = start_seg.get("start", 0.0)
            start_text = start_seg.get("text", "").lower()

            # Hook score calculation
            hook_score = 70.0
            if any(kw in start_text for kw in HOOK_KEYWORDS):
                hook_score += 20.0
            if "?" in start_text or "!" in start_text:
                hook_score += 8.0
            hook_score = min(98.0, hook_score)

            # Slide forward to find target duration boundary
            accumulated_text = []
            for j in range(i, num_segments):
                seg = transcript_segments[j]
                end_time = seg.get("end", start_time + 30.0)
                seg_text = seg.get("text", "")
                accumulated_text.append(seg_text)
                cur_duration = end_time - start_time

                if cur_duration >= target_min:
                    combined_text = " ".join(accumulated_text).lower()
                    
                    # Payoff score
                    payoff_score = 68.0
                    if any(kw in seg_text.lower() for kw in PAYOFF_KEYWORDS):
                        payoff_score += 22.0
                    if "." in seg_text or "!" in seg_text:
                        payoff_score += 6.0
                    payoff_score = min(96.0, payoff_score)

                    # Story & retention
                    story_score = min(95.0, 72.0 + (len(combined_text) % 20))
                    curiosity_score = min(98.0, hook_score * 0.95 + 4.0)
                    retention_score = min(96.0, (hook_score + payoff_score) / 2.0 + 3.0)
                    emotion_score = min(94.0, 75.0 + (i % 15))
                    shareability_score = min(95.0, 76.0 + (j % 18))
                    novelty_score = min(92.0, 74.0 + ((i + j) % 15))
                    quotability_score = min(96.0, 75.0 + ((j * 3) % 20))

                    first_sentence = (start_seg.get("text", "").strip() or "Compelling opening hook")
                    last_sentence = (seg.get("text", "").strip() or "Climactic ending insight")

                    candidates.append(
                        RawCandidateMoment(
                            start=round(start_time, 2),
                            end=round(end_time, 2),
                            hook_score=round(hook_score, 1),
                            retention_score=round(retention_score, 1),
                            curiosity_score=round(curiosity_score, 1),
                            emotion_score=round(emotion_score, 1),
                            story_score=round(story_score, 1),
                            payoff_score=round(payoff_score, 1),
                            shareability_score=round(shareability_score, 1),
                            novelty_score=round(novelty_score, 1),
                            quotability_score=round(quotability_score, 1),
                            standalone_score=round(min(98.0, story_score * 0.95 + 4.0), 1),
                            rewatch_score=round(min(96.0, (hook_score + emotion_score) / 2.0), 1),
                            visual_score=82.0,
                            audio_score=86.0,
                            platform_score=88.0,
                            reason=f"Strong {mode} hook '{first_sentence[:40]}...' with impactful resolution.",
                            hook_summary=first_sentence[:80],
                            payoff_summary=last_sentence[:80],
                        )
                    )

                if cur_duration > target_max:
                    break

        # If candidates are too few, create default segments across video timeline
        needed_pool = max(requested_count * 3, 15)
        if len(candidates) < needed_pool:
            total_dur = media_info.get("duration_seconds", 60.0)
            seg_len = min(target_max, max(target_min, total_dur / max(1, requested_count)))
            step = max(5.0, (total_dur - seg_len) / max(1, needed_pool))
            t = 0.0
            idx = 1
            while t + 10.0 <= total_dur and len(candidates) < needed_pool:
                cand_end = min(t + seg_len, total_dur)
                if cand_end > t + 5.0:
                    candidates.append(
                        RawCandidateMoment(
                            start=round(t, 2),
                            end=round(cand_end, 2),
                            hook_score=min(96.0, 80.0 + (idx * 3 % 15)),
                            retention_score=min(94.0, 82.0 + (idx * 2 % 12)),
                            curiosity_score=min(95.0, 81.0 + (idx * 4 % 14)),
                            emotion_score=min(92.0, 78.0 + (idx * 3 % 14)),
                            story_score=min(95.0, 84.0 + (idx * 2 % 10)),
                            payoff_score=min(96.0, 83.0 + (idx * 3 % 13)),
                            shareability_score=82.0,
                            novelty_score=78.0,
                            quotability_score=80.0,
                            standalone_score=85.0,
                            rewatch_score=80.0,
                            visual_score=82.0,
                            audio_score=85.0,
                            platform_score=86.0,
                            reason=f"Cohesive {mode} thematic moment #{idx} with strong narrative progression.",
                            hook_summary=f"Key highlight starting at {int(t)}s",
                            payoff_summary=f"Climax payoff ending at {int(cand_end)}s",
                        )
                    )
                    idx += 1
                t += step

        return candidates


    async def rank_candidates(
        self,
        candidates: List[RawCandidateMoment],
        transcript_context: str,
    ) -> List[RawCandidateMoment]:
        return sorted(
            candidates,
            key=lambda c: (c.hook_score * 0.3 + c.retention_score * 0.3 + c.payoff_score * 0.4),
            reverse=True,
        )

    async def generate_metadata(
        self,
        clip_transcript: str,
        clip_context: Dict[str, Any],
    ) -> PlatformClipMetadata:
        hook = clip_context.get("hook_summary", "Unbelievable Insight")
        first_words = " ".join(clip_transcript.split()[:8])
        clean_title = (hook if len(hook) > 10 else first_words) or "Must-Watch Short"

        return PlatformClipMetadata(
            tiktok_title=clean_title[:80],
            tiktok_caption=f"{clean_title} 🤯 You won't believe what happens next. #fyp #viral #shorts #mustwatch",
            tiktok_hashtags=["#fyp", "#viral", "#shortform", "#storytime", "#trending"],
            reels_caption=f"{clean_title}\n\nDid you know this? Drop your thoughts below! 👇\n\n📌 Save for later | 📲 Share with a friend",
            reels_hashtags=["#reels", "#explorepage", "#viralreels", "#mindset", "#dailyinspiration"],
            shorts_title=f"{clean_title[:50]} #shorts",
            shorts_description=f"{clip_transcript[:180]}...\n\nSubscribe for daily short-form content!",
            shorts_hashtags=["#shorts", "#viral", "#trending", "#insights"],
        )

    async def analyze_visual_context(self, frame_paths: List[str]) -> Dict[str, Any]:
        return {"visual_engagement": 84.0, "face_detected": True}
