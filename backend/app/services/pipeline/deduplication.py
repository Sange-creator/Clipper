"""Deduplication and Non-Maximum Suppression (NMS) for short-form clips."""

import logging
from typing import List, Tuple
from app.services.ai.base import RawCandidateMoment

logger = logging.getLogger(__name__)


def compute_temporal_iou(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """Calculates Intersection over Union (IoU) of two temporal intervals."""
    intersection_start = max(a_start, b_start)
    intersection_end = min(a_end, b_end)
    intersection = max(0.0, intersection_end - intersection_start)

    union_start = min(a_start, b_start)
    union_end = max(a_end, b_end)
    union = max(0.1, union_end - union_start)

    return intersection / union


def compute_overlap_ratio(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """Calculates the ratio of overlap relative to the shorter clip."""
    intersection_start = max(a_start, b_start)
    intersection_end = min(a_end, b_end)
    intersection = max(0.0, intersection_end - intersection_start)
    shorter_duration = max(0.1, min(a_end - a_start, b_end - b_start))
    return intersection / shorter_duration


class DeduplicationService:
    """Removes heavily overlapping moments while guaranteeing requested yield."""

    def deduplicate_candidates(
        self,
        candidates_with_scores: List[Tuple[RawCandidateMoment, float, float]],
        iou_threshold: float = 0.45,
        max_overlap_ratio: float = 0.55,
        min_keep_count: int = 1,
    ) -> List[Tuple[RawCandidateMoment, float, float]]:
        """
        Two-stage Non-Maximum Suppression (NMS) with guaranteed yield:
        Pass 1: Strictly selects distinct non-overlapping candidate peaks.
        Pass 2: If accepted < min_keep_count, backfills with the best diverse non-identical candidates.
        """
        # Sort by composite score descending
        sorted_candidates = sorted(candidates_with_scores, key=lambda x: x[1], reverse=True)
        accepted: List[Tuple[RawCandidateMoment, float, float]] = []
        unaccepted: List[Tuple[RawCandidateMoment, float, float]] = []

        # Pass 1: Strict NMS
        for candidate, comp_score, penalty in sorted_candidates:
            keep = True
            for acc_candidate, _, _ in accepted:
                iou = compute_temporal_iou(candidate.start, candidate.end, acc_candidate.start, acc_candidate.end)
                overlap_ratio = compute_overlap_ratio(candidate.start, candidate.end, acc_candidate.start, acc_candidate.end)

                if iou > iou_threshold or overlap_ratio > max_overlap_ratio:
                    keep = False
                    break

            if keep:
                accepted.append((candidate, comp_score, penalty))
            else:
                unaccepted.append((candidate, comp_score, penalty))

        # Pass 2: Guaranteed yield backfill
        if len(accepted) < min_keep_count and unaccepted:
            for candidate, comp_score, penalty in unaccepted:
                # Ensure not an exact duplicate (start diff >= 2.0s or iou < 0.80)
                is_duplicate = False
                for acc_candidate, _, _ in accepted:
                    iou = compute_temporal_iou(candidate.start, candidate.end, acc_candidate.start, acc_candidate.end)
                    start_diff = abs(candidate.start - acc_candidate.start)
                    if iou > 0.80 or start_diff < 2.0:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    accepted.append((candidate, comp_score, penalty))
                    if len(accepted) >= min_keep_count:
                        break

        logger.info(f"Deduplication: Reduced candidate pool from {len(candidates_with_scores)} to {len(accepted)} diverse clips (target min: {min_keep_count}).")
        return accepted


deduplication_service = DeduplicationService()
