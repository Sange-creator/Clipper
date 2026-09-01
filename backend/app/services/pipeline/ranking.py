"""Global candidate ranking and cross-video project diversity engine."""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from app.services.ai.base import RawCandidateMoment

logger = logging.getLogger(__name__)


class RankingService:
    """Ranks diverse candidates globally across single videos or multi-video projects."""

    def rank_and_select(
        self,
        deduplicated_candidates: List[Tuple[RawCandidateMoment, float, float]],
        target_count: int,
        duration_preset: str = "30-45s",
    ) -> List[Tuple[RawCandidateMoment, float, float, int]]:
        """Single video ranking respecting user duration constraints."""
        target_min, target_max = self._get_duration_bounds(duration_preset)

        scored_candidates = []
        for candidate, comp_score, penalty in deduplicated_candidates:
            duration = candidate.end - candidate.start
            adjusted_score = comp_score

            if duration < target_min:
                adjusted_score -= min(15.0, (target_min - duration) * 0.8)
            elif duration > target_max:
                adjusted_score -= min(15.0, (duration - target_max) * 0.5)

            if candidate.story_score >= 88.0 and candidate.payoff_score >= 88.0:
                adjusted_score += 3.0

            scored_candidates.append((candidate, round(adjusted_score, 2), penalty))

        sorted_top = sorted(scored_candidates, key=lambda x: x[1], reverse=True)
        selected_pool = sorted_top[:target_count]

        ranked_results = []
        for rank, (cand, final_score, pen) in enumerate(selected_pool, start=1):
            ranked_results.append((cand, final_score, pen, rank))

        logger.info(f"Ranking: Selected top {len(ranked_results)} clips (requested {target_count}).")
        return ranked_results

    def cross_video_global_rank(
        self,
        video_candidates_map: Dict[str, List[Tuple[RawCandidateMoment, float, float]]],
        target_count: int,
        duration_preset: str = "30-45s",
        source_diversity_weight: float = 0.35,
    ) -> List[Tuple[str, RawCandidateMoment, float, float, int]]:
        """
        Cross-Video Global Ranking using Greedy Diversity Selection:
        Combines candidates from all videos in a project and dynamically balances
        source representation using diversity penalties while prioritizing quality.
        """
        target_min, target_max = self._get_duration_bounds(duration_preset)

        # Build candidate pool with adjusted base scores
        pool: List[Dict[str, Any]] = []
        for video_id, cand_list in video_candidates_map.items():
            for cand, score, pen in cand_list:
                dur = cand.end - cand.start
                adj_score = score
                if dur < target_min:
                    adj_score -= min(15.0, (target_min - dur) * 0.8)
                elif dur > target_max:
                    adj_score -= min(15.0, (dur - target_max) * 0.5)

                if cand.story_score >= 88.0 and cand.payoff_score >= 88.0:
                    adj_score += 3.0

                pool.append({
                    "video_id": video_id,
                    "candidate": cand,
                    "base_score": round(adj_score, 2),
                    "penalty": pen,
                })

        selected: List[Tuple[str, RawCandidateMoment, float, float]] = []
        source_counts: Dict[str, int] = defaultdict(int)

        # Iteratively pick candidate with highest diversity-penalized score
        while pool and len(selected) < target_count:
            best_idx = -1
            best_effective_score = -9999.0

            for i, item in enumerate(pool):
                vid = item["video_id"]
                count = source_counts[vid]
                div_penalty = count * (source_diversity_weight * 12.0)
                eff_score = item["base_score"] - div_penalty
                if eff_score > best_effective_score:
                    best_effective_score = eff_score
                    best_idx = i

            if best_idx == -1:
                break

            chosen = pool.pop(best_idx)
            selected.append((
                chosen["video_id"],
                chosen["candidate"],
                chosen["base_score"],
                chosen["penalty"],
            ))
            source_counts[chosen["video_id"]] += 1

        results: List[Tuple[str, RawCandidateMoment, float, float, int]] = []
        for rank, (vid, cand, score, pen) in enumerate(selected, start=1):
            results.append((vid, cand, score, pen, rank))

        logger.info(
            f"Cross-Video Global Ranking: Selected top {len(results)} clips from {len(video_candidates_map)} sources."
        )
        return results

    def _get_duration_bounds(self, duration_preset: str) -> Tuple[float, float]:
        if "15-30" in duration_preset:
            return 14.0, 34.0
        elif "30-45" in duration_preset:
            return 26.0, 50.0
        elif "45-60" in duration_preset:
            return 40.0, 68.0
        elif "60-90" in duration_preset:
            return 55.0, 100.0
        return 15.0, 50.0


ranking_service = RankingService()
