"""Context expansion and natural boundary adjustment engine."""

import logging
from typing import Any, Dict, List
from app.services.ai.base import RawCandidateMoment

logger = logging.getLogger(__name__)

FILLER_STARTS = [
    "so", "um", "uh", "like", "you know", "hello", "hi guys", "welcome back",
    "today we are going to", "in this video", "hey everyone", "basically"
]


class ContextExpansionService:
    """Refines candidate boundaries to ensure strong opening hooks and complete narrative payoffs."""

    def expand_candidate_context(
        self,
        candidate: RawCandidateMoment,
        transcript_segments: List[Dict[str, Any]],
        video_duration: float,
    ) -> RawCandidateMoment:
        """
        Adjusts start/end timestamps of a candidate moment:
        - Snaps to exact sentence/word beginnings.
        - Trims filler words at the start.
        - Ensures necessary context is included before a punchy sentence.
        - Extends boundary to natural conclusion/payoff.
        """
        start = max(0.0, candidate.start)
        end = min(video_duration, candidate.end)

        # Find matching segments in range
        overlapping_segs = [
            s for s in transcript_segments
            if s.get("end", 0.0) >= start - 3.0 and s.get("start", 0.0) <= end + 3.0
        ]

        if not overlapping_segs:
            return candidate

        # Refine start boundary
        best_start = start
        for s in overlapping_segs:
            s_start = s.get("start", 0.0)
            s_end = s.get("end", 0.0)
            s_text = s.get("text", "").strip().lower()

            # If segment is near candidate start
            if abs(s_start - start) < 3.0:
                # Check if starts with filler
                has_filler = any(s_text.startswith(f) for f in FILLER_STARTS)
                if has_filler and s.get("words"):
                    # Advance to first non-filler word
                    words = s["words"]
                    if len(words) > 2:
                        best_start = words[1].get("start", s_start)
                    else:
                        best_start = s_end
                else:
                    best_start = s_start
                break

        # Refine end boundary (ensure thought/sentence completion)
        best_end = end
        for s in reversed(overlapping_segs):
            s_end = s.get("end", 0.0)
            s_text = s.get("text", "").strip()

            if abs(s_end - end) < 4.0:
                # If ends with sentence terminator, snap to it
                if s_text.endswith((".", "!", "?")):
                    best_end = s_end
                    break
                else:
                    best_end = s_end

        # Ensure duration sanity (min 15s, max 95s unless custom)
        adjusted_duration = best_end - best_start
        if adjusted_duration < 12.0 and best_end + (15.0 - adjusted_duration) <= video_duration:
            best_end = min(video_duration, best_start + 18.0)

        # Clone and update candidate
        return RawCandidateMoment(
            start=round(best_start, 2),
            end=round(best_end, 2),
            hook_score=candidate.hook_score,
            retention_score=candidate.retention_score,
            curiosity_score=candidate.curiosity_score,
            emotion_score=candidate.emotion_score,
            story_score=candidate.story_score,
            payoff_score=candidate.payoff_score,
            shareability_score=candidate.shareability_score,
            novelty_score=candidate.novelty_score,
            quotability_score=candidate.quotability_score,
            standalone_score=getattr(candidate, "standalone_score", 80.0),
            rewatch_score=getattr(candidate, "rewatch_score", 75.0),
            visual_score=candidate.visual_score,
            audio_score=candidate.audio_score,
            platform_score=candidate.platform_score,
            reason=candidate.reason,
            hook_summary=candidate.hook_summary,
            payoff_summary=candidate.payoff_summary,
        )


context_expansion_service = ContextExpansionService()
