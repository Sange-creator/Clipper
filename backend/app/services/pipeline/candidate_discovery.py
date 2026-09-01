"""Candidate discovery engine generating a massive candidate moment pool."""

import logging
from typing import Any, Dict, List, Optional
from app.services.ai.base import AIProvider, RawCandidateMoment

logger = logging.getLogger(__name__)


class CandidateDiscoveryService:
    """Discovers high-potential short-form candidate moments from transcript & media context."""

    async def discover_candidates(
        self,
        ai_provider: AIProvider,
        transcript_segments: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        requested_clips_count: int,
        duration_preset: str = "30-45s",
        mode: str = "podcast",
        custom_instructions: Optional[str] = None,
    ) -> List[RawCandidateMoment]:
        """
        Discovers an oversized candidate pool (e.g. 5x - 10x of requested count)
        to enable competitive scoring, deduplication, and diversity filtering.
        """
        pool_size = max(requested_clips_count * 5, 40)
        logger.info(f"Generating candidate pool of size {pool_size} for {requested_clips_count} requested clips in mode '{mode}'.")

        try:
            candidates = await ai_provider.generate_candidates(
                transcript_segments=transcript_segments,
                media_info=media_info,
                requested_count=requested_clips_count,
                duration_target=duration_preset,
                mode=mode,
                custom_instructions=custom_instructions,
            )
            if candidates and len(candidates) > 0:
                logger.info(f"AI Provider returned {len(candidates)} raw candidate moments.")
                return candidates
        except Exception as e:
            logger.warning(f"Primary discovery failed: {e}. Executing safety fallback...")

        # Fallback to local heuristic candidate generation
        from app.services.ai.mock import MockAIProvider
        logger.info("Using Local Heuristic AI Provider as final safety net.")
        return await MockAIProvider().generate_candidates(
            transcript_segments=transcript_segments,
            media_info=media_info,
            requested_count=requested_clips_count,
            duration_target=duration_preset,
            mode=mode,
            custom_instructions=custom_instructions,
        )


candidate_discovery_service = CandidateDiscoveryService()

