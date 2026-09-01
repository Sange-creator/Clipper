"""Unit tests for cross-video global candidate ranking and source diversity."""

from app.services.ai.base import RawCandidateMoment
from app.services.pipeline.ranking import ranking_service


def test_cross_video_global_ranking_source_diversity():
    # Video A: 3 high scoring candidates
    vA_candidates = [
        (RawCandidateMoment(start=10.0, end=45.0, hook_score=95, retention_score=92, story_score=90, payoff_score=90), 94.0, 0.0),
        (RawCandidateMoment(start=60.0, end=95.0, hook_score=92, retention_score=90, story_score=90, payoff_score=90), 91.0, 0.0),
        (RawCandidateMoment(start=120.0, end=155.0, hook_score=90, retention_score=89, story_score=88, payoff_score=88), 89.0, 0.0),
    ]

    # Video B: 2 medium-high scoring candidates
    vB_candidates = [
        (RawCandidateMoment(start=15.0, end=50.0, hook_score=88, retention_score=87, story_score=88, payoff_score=88), 88.0, 0.0),
        (RawCandidateMoment(start=70.0, end=105.0, hook_score=85, retention_score=84, story_score=85, payoff_score=85), 85.0, 0.0),
    ]

    video_map = {
        "vid_A": vA_candidates,
        "vid_B": vB_candidates,
    }

    # Request top 3 with source diversity weighting
    results = ranking_service.cross_video_global_rank(
        video_candidates_map=video_map,
        target_count=3,
        duration_preset="30-45s",
        source_diversity_weight=0.35,
    )

    assert len(results) == 3
    sources = [r[0] for r in results]
    # Both sources should be represented rather than only vid_A
    assert "vid_A" in sources
    assert "vid_B" in sources
    assert results[0][4] == 1  # Rank #1
    assert results[1][4] == 2  # Rank #2
    assert results[2][4] == 3  # Rank #3
