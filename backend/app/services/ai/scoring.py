"""Scoring engine implementing GEMINI.md 12-dimensional composite scoring & penalty algorithms."""

from typing import Dict, Optional
from app.config import settings
from app.services.ai.base import RawCandidateMoment


class CandidateScorer:
    """Calculates weighted composite score and applies multi-dimensional penalties."""

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        self.weights = custom_weights or settings.SCORING_WEIGHTS

    def calculate_composite_score(self, candidate: RawCandidateMoment, duration: float, has_speech_gap: bool = False, speech_clarity: float = 1.0) -> tuple[float, float]:
        """
        Calculates the normalized composite score (0-100) and the penalty deduction.
        Returns (composite_score, penalty_deductions).
        """
        # Base weighted score (V3 12-factor weights summing to 1.00)
        standalone = getattr(candidate, "standalone_score", candidate.story_score)
        rewatch = getattr(candidate, "rewatch_score", candidate.retention_score)

        raw_weighted = (
            candidate.hook_score * self.weights.get("hook", 0.16) +
            candidate.retention_score * self.weights.get("retention", 0.15) +
            candidate.curiosity_score * self.weights.get("curiosity", 0.12) +
            candidate.story_score * self.weights.get("story", 0.10) +
            candidate.payoff_score * self.weights.get("payoff", 0.10) +
            candidate.emotion_score * self.weights.get("emotion", 0.08) +
            candidate.shareability_score * self.weights.get("shareability", 0.08) +
            standalone * self.weights.get("standalone", 0.07) +
            candidate.novelty_score * self.weights.get("novelty", 0.05) +
            candidate.quotability_score * self.weights.get("quotability", 0.04) +
            rewatch * self.weights.get("rewatch", 0.03) +
            candidate.visual_score * self.weights.get("visual", 0.01) +
            candidate.audio_score * self.weights.get("audio", 0.01)
        )

        penalties = 0.0

        # 1. Weak Opening Penalty: First seconds matter heavily.
        if candidate.hook_score < 40.0:
            penalties += 20.0 + (40.0 - candidate.hook_score) * 0.5
        elif candidate.hook_score < 60.0:
            penalties += (60.0 - candidate.hook_score) * 0.6

        # 2. Weak Payoff Penalty: Incomplete ending
        if candidate.payoff_score < 40.0:
            penalties += 15.0 + (40.0 - candidate.payoff_score) * 0.4
        elif candidate.payoff_score < 60.0:
            penalties += (60.0 - candidate.payoff_score) * 0.4

        # 3. Story Completeness Penalty: Missing context
        if candidate.story_score < 40.0:
            penalties += 15.0 + (40.0 - candidate.story_score) * 0.4
        elif candidate.story_score < 60.0:
            penalties += (60.0 - candidate.story_score) * 0.4

        # 4. Excessive silence or pauses
        if has_speech_gap:
            penalties += 8.0

        # 5. Low speech clarity / confidence
        if speech_clarity < 0.7:
            penalties += (0.7 - speech_clarity) * 20.0

        # 6. Extreme duration boundary penalties (e.g. under 10 seconds or over 180 seconds)
        if duration < 12.0:
            penalties += 15.0
        elif duration > 150.0:
            penalties += 10.0

        # Clamp composite score between 0.0 and 100.0
        final_score = max(0.0, min(100.0, raw_weighted - penalties))
        return round(final_score, 2), round(penalties, 2)


scorer = CandidateScorer()
