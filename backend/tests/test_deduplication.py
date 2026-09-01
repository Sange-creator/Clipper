"""Tests for temporal IoU and Non-Maximum Suppression (NMS) deduplication."""

import pytest
from app.services.ai.base import RawCandidateMoment
from app.services.pipeline.deduplication import (
    DeduplicationService,
    compute_overlap_ratio,
    compute_temporal_iou,
)


def test_temporal_iou_calculation():
    # Exact match -> 1.0
    assert compute_temporal_iou(0.0, 30.0, 0.0, 30.0) == 1.0
    # No overlap -> 0.0
    assert compute_temporal_iou(0.0, 20.0, 30.0, 50.0) == 0.0
    # Partial overlap (10s overlap / 30s union = 0.333)
    iou = compute_temporal_iou(0.0, 20.0, 10.0, 30.0)
    assert 0.33 <= iou <= 0.34


def test_deduplication_filters_overlapping_moments():
    dedup = DeduplicationService()
    cand1 = RawCandidateMoment(start=10.0, end=40.0, hook_score=95.0, reason="High score moment")
    cand2 = RawCandidateMoment(start=12.0, end=42.0, hook_score=80.0, reason="Duplicate moment")
    cand3 = RawCandidateMoment(start=60.0, end=90.0, hook_score=85.0, reason="Independent moment")

    candidates_with_scores = [
        (cand1, 92.0, 0.0),
        (cand2, 78.0, 0.0),
        (cand3, 84.0, 0.0),
    ]

    result = dedup.deduplicate_candidates(candidates_with_scores, iou_threshold=0.4)
    # cand2 overlaps heavily with cand1 and has lower score, so it should be suppressed
    assert len(result) == 2
    assert result[0][0].start == 10.0
    assert result[1][0].start == 60.0


def test_deduplication_guaranteed_yield_when_requesting_three_clips():
    dedup = DeduplicationService()
    cand1 = RawCandidateMoment(start=0.0, end=30.0, hook_score=95.0, reason="Opening climax")
    cand2 = RawCandidateMoment(start=10.0, end=40.0, hook_score=88.0, reason="Midpoint escalation")
    cand3 = RawCandidateMoment(start=20.0, end=50.0, hook_score=85.0, reason="Ending resolution")

    candidates_with_scores = [
        (cand1, 95.0, 0.0),
        (cand2, 88.0, 0.0),
        (cand3, 85.0, 0.0),
    ]

    # Without guaranteed yield, candidates 2 and 3 might be dropped by strict NMS
    strict_result = dedup.deduplicate_candidates(candidates_with_scores, iou_threshold=0.3, min_keep_count=1)
    
    # With guaranteed yield min_keep_count=3, all 3 distinct offset clips are preserved
    guaranteed_result = dedup.deduplicate_candidates(candidates_with_scores, iou_threshold=0.3, min_keep_count=3)
    assert len(guaranteed_result) == 3
    starts = {r[0].start for r in guaranteed_result}
    assert starts == {0.0, 10.0, 20.0}

