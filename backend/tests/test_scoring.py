"""Tests for 12-dimensional composite scoring and penalty math."""

import pytest
from app.services.ai.base import RawCandidateMoment
from app.services.ai.scoring import CandidateScorer


def test_perfect_candidate_score():
    scorer = CandidateScorer()
    cand = RawCandidateMoment(
        start=0.0,
        end=30.0,
        hook_score=100.0,
        retention_score=100.0,
        curiosity_score=100.0,
        emotion_score=100.0,
        story_score=100.0,
        payoff_score=100.0,
        shareability_score=100.0,
        novelty_score=100.0,
        quotability_score=100.0,
        visual_score=100.0,
        audio_score=100.0,
        platform_score=100.0,
    )
    score, penalties = scorer.calculate_composite_score(cand, duration=30.0)
    assert score >= 98.0
    assert penalties == 0.0


def test_weak_hook_penalty():
    scorer = CandidateScorer()
    cand = RawCandidateMoment(
        start=0.0,
        end=30.0,
        hook_score=35.0,  # Weak opening
        retention_score=80.0,
        curiosity_score=80.0,
        emotion_score=80.0,
        story_score=80.0,
        payoff_score=80.0,
        shareability_score=80.0,
        novelty_score=80.0,
        quotability_score=80.0,
    )
    score, penalties = scorer.calculate_composite_score(cand, duration=30.0)
    assert penalties > 20.0
    assert score < 60.0


def test_excessive_duration_penalty():
    scorer = CandidateScorer()
    cand = RawCandidateMoment(
        start=0.0,
        end=8.0,  # Under 10 seconds
        hook_score=90.0,
        retention_score=90.0,
        curiosity_score=90.0,
        emotion_score=90.0,
        story_score=90.0,
        payoff_score=90.0,
        shareability_score=90.0,
    )
    score, penalties = scorer.calculate_composite_score(cand, duration=8.0)
    assert penalties >= 15.0
