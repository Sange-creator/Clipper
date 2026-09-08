"""Context expansion and natural boundary adjustment engine."""

import logging
import re
from typing import Any, Dict, List
from app.services.ai.base import RawCandidateMoment

logger = logging.getLogger(__name__)

FILLER_STARTS = [
    "so", "um", "uh", "like", "you know", "hello", "hi guys", "welcome back",
    "today we are going to", "in this video", "hey everyone", "basically", "well",
    "yeah", "okay", "alright", "and so", "but anyway"
]

FILLER_WORDS = {
    "so", "um", "uh", "like", "well", "basically", "and", "but", "now",
    "hey", "hello", "hi", "right", "yeah", "okay", "alright"
}


class ContextExpansionService:
    """Refines candidate boundaries to ensure strong opening hooks and complete narrative payoffs."""

    def snap_to_hook(self, start: float, transcript_segments: List[Dict[str, Any]]) -> float:
        """
        Locates the exact word/sentence beginning at or immediately after `start`:
        - Strips leading filler words ('so', 'um', 'uh', 'like', 'well', 'basically', 'yeah').
        - Never drags start time backwards into preceding sentences or preambles.
        """
        target_s = max(0.0, float(start))
        if not transcript_segments:
            return target_s

        # Find words in proximity [target_s - 0.35, target_s + 4.0]
        nearby_words: List[Dict[str, Any]] = []
        for s in transcript_segments:
            s_s = float(s.get("start", 0.0))
            s_e = float(s.get("end", 0.0))
            if s_e >= target_s - 0.5 and s_s <= target_s + 5.0:
                words = s.get("words", [])
                if words:
                    nearby_words.extend(words)

        if nearby_words:
            # Sort words chronologically
            nearby_words.sort(key=lambda w: float(w.get("start", 0.0)))
            # Find the first word that starts at or slightly around target_s
            cand_words = [w for w in nearby_words if float(w.get("start", 0.0)) >= target_s - 0.35]
            if cand_words:
                idx = 0
                while idx < len(cand_words) and idx < 4:
                    w = cand_words[idx]
                    w_clean = re.sub(r"[^\w]", "", w.get("word", "").lower())
                    if w_clean in FILLER_WORDS and idx + 1 < len(cand_words):
                        idx += 1
                        continue
                    return round(max(0.0, float(w.get("start", target_s))), 2)

        # Fallback: inspect segment containing target_s
        for s in transcript_segments:
            s_s = float(s.get("start", 0.0))
            s_e = float(s.get("end", 0.0))
            if s_s <= target_s <= s_e or (target_s - 0.3 <= s_s <= target_s + 0.8):
                # If segment started before target_s, only snap to s_s if very close (<0.3s)
                if abs(s_s - target_s) <= 0.3:
                    text = s.get("text", "").strip().lower()
                    if not any(text.startswith(f) for f in FILLER_STARTS):
                        return round(max(0.0, s_s), 2)
                return round(target_s, 2)

        return round(target_s, 2)

    def expand_candidate_context(
        self,
        candidate: RawCandidateMoment,
        transcript_segments: List[Dict[str, Any]],
        video_duration: float,
        custom_min_duration: float | None = None,
        custom_max_duration: float | None = None,
    ) -> RawCandidateMoment:
        """
        Adjusts start/end timestamps of a candidate moment:
        - Snaps to exact sentence/word beginnings using snap_to_hook.
        - Trims filler words at the start.
        - Ensures necessary context is included before a punchy sentence.
        - Extends boundary to natural conclusion/payoff.
        - Respects custom min/max durations when supplied.
        """
        start = max(0.0, candidate.start)
        end = min(video_duration, candidate.end)

        # Find matching segments in range
        overlapping_segs = [
            s for s in transcript_segments
            if s.get("end", 0.0) >= start - 1.0 and s.get("start", 0.0) <= end + 4.0
        ]

        if not overlapping_segs:
            return candidate

        # Snap start boundary precisely to hook without dragging backwards into preamble
        best_start = self.snap_to_hook(start, transcript_segments)

        # Refine end boundary (ensure thought/sentence completion)
        best_end = end
        for s in reversed(overlapping_segs):
            s_end = float(s.get("end", 0.0))
            s_text = s.get("text", "").strip()

            if abs(s_end - end) < 4.0:
                # If ends with sentence terminator, snap to it
                if s_text.endswith((".", "!", "?")):
                    best_end = s_end
                    break
                else:
                    best_end = s_end

        # Duration bounds
        min_d = float(custom_min_duration or 14.0)
        max_d = float(custom_max_duration or 75.0)
        if max_d < min_d:
            max_d = min_d + 15.0

        adjusted_duration = best_end - best_start
        if adjusted_duration < min_d and best_start + min_d <= video_duration:
            best_end = min(video_duration, best_start + min_d)
        elif adjusted_duration > max_d:
            best_end = best_start + max_d

        # Clone and update candidate
        return RawCandidateMoment(
            start=round(best_start, 2),
            end=round(best_end, 2),
            climax_start=getattr(candidate, "climax_start", None),
            climax_end=getattr(candidate, "climax_end", None),
            climax_summary=getattr(candidate, "climax_summary", None),
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

