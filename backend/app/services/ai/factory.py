"""AI Provider Factory with dynamic configuration, multi-API orchestration, and automatic fallback chaining."""

import logging
from typing import Any, Dict, List, Optional
from app.config import settings
from app.services.ai.base import (
    AIProvider,
    RawCandidateMoment,
    ContentAnalysisResult,
    PlatformClipMetadata,
)
from app.services.ai.gemini import GeminiProvider
from app.services.ai.groq import GroqProvider
from app.services.ai.mock import MockAIProvider

logger = logging.getLogger(__name__)


class ResilientAIProvider(AIProvider):
    """
    High-resilience composite AI Provider that automatically handles provider failures,
    rate limits (429), authentication errors (401/403), and network timeouts by failing
    over to the next configured provider in the resilience chain.
    """

    def __init__(self, primary_name: Optional[str] = None):
        self.providers: List[AIProvider] = []
        self._setup_providers(primary_name)

    def _setup_providers(self, primary_name: Optional[str]):
        chosen = (primary_name or settings.AI_PROVIDER or "groq").lower()

        provider_instances: Dict[str, AIProvider] = {}
        if settings.GROQ_API_KEY:
            try:
                provider_instances["groq"] = GroqProvider()
            except Exception as e:
                logger.warning(f"Could not init GroqProvider: {e}")

        if settings.GEMINI_API_KEY:
            try:
                provider_instances["gemini"] = GeminiProvider()
            except Exception as e:
                logger.warning(f"Could not init GeminiProvider: {e}")

        provider_instances["mock"] = MockAIProvider()

        # Order chain based on preference
        if chosen == "groq":
            chain = ["groq", "gemini", "mock"]
        elif chosen == "gemini":
            chain = ["gemini", "groq", "mock"]
        else:
            chain = ["mock", "groq", "gemini"]

        for name in chain:
            if name in provider_instances and provider_instances[name] not in self.providers:
                self.providers.append(provider_instances[name])

        if not self.providers:
            self.providers.append(MockAIProvider())

        logger.info(f"Initialized ResilientAIProvider with chain: {[p.__class__.__name__ for p in self.providers]}")

    async def analyze_content(self, transcript: str, media_info: Dict[str, Any]) -> ContentAnalysisResult:
        for provider in self.providers:
            try:
                return await provider.analyze_content(transcript, media_info)
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__}.analyze_content failed: {e}. Trying fallback...")
        return ContentAnalysisResult(summary="Video content analysis", main_topics=["Shorts"], tone="engaging")

    async def generate_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        requested_count: int,
        duration_target: str = "30-45s",
        mode: str = "podcast",
        custom_instructions: Optional[str] = None,
    ) -> List[RawCandidateMoment]:
        last_error = None
        for provider in self.providers:
            try:
                logger.info(f"Attempting candidate discovery using {provider.__class__.__name__} in mode '{mode}'...")
                results = await provider.generate_candidates(
                    transcript_segments=transcript_segments,
                    media_info=media_info,
                    requested_count=requested_count,
                    duration_target=duration_target,
                    mode=mode,
                    custom_instructions=custom_instructions,
                )
                if results and len(results) > 0:
                    logger.info(f"{provider.__class__.__name__} succeeded with {len(results)} candidate moments.")
                    return results
            except Exception as e:
                last_error = e
                logger.warning(
                    f"{provider.__class__.__name__}.generate_candidates failed: {e}. "
                    f"Failing over to next provider in resilience chain..."
                )

        # If all fail, use deterministic fallback
        logger.warning(f"All primary providers failed (last error: {last_error}). Using deterministic safety net.")
        return await MockAIProvider().generate_candidates(
            transcript_segments=transcript_segments,
            media_info=media_info,
            requested_count=requested_count,
            duration_target=duration_target,
            mode=mode,
            custom_instructions=custom_instructions,
        )

    async def rank_candidates(
        self,
        candidates: List[RawCandidateMoment],
        transcript_context: str,
    ) -> List[RawCandidateMoment]:
        for provider in self.providers:
            try:
                return await provider.rank_candidates(candidates, transcript_context)
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__}.rank_candidates failed: {e}. Trying fallback...")
        return await MockAIProvider().rank_candidates(candidates, transcript_context)

    async def generate_metadata(
        self,
        clip_transcript: str,
        clip_context: Dict[str, Any],
    ) -> PlatformClipMetadata:
        for provider in self.providers:
            try:
                return await provider.generate_metadata(clip_transcript, clip_context)
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__}.generate_metadata failed: {e}. Trying fallback...")
        return await MockAIProvider().generate_metadata(clip_transcript, clip_context)

    async def analyze_visual_context(self, frame_paths: List[str]) -> Dict[str, Any]:
        for provider in self.providers:
            try:
                return await provider.analyze_visual_context(frame_paths)
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__}.analyze_visual_context failed: {e}. Trying fallback...")
        return {"visual_engagement": 80.0, "face_detected": True}


class HybridOrchestratedAIProvider(AIProvider):
    """
    Best-of-Breed Multi-API Orchestration Engine.
    Assigns each AI provider to what it performs best at:
    - Candidate Discovery: Groq (ultra-low latency candidate generation across large transcripts)
    - Multimodal & Visual Context: Gemini (native multimodal understanding)
    - Viral Social Copywriting & Metadata: Gemini (creative human-like titles, captions, hashtags)
    - Full fallback chaining to ensure zero job failures.
    """

    def __init__(self):
        self.groq_provider: Optional[AIProvider] = None
        self.gemini_provider: Optional[AIProvider] = None
        self.mock_provider = MockAIProvider()

        if settings.GROQ_API_KEY:
            try:
                self.groq_provider = GroqProvider()
            except Exception as e:
                logger.warning(f"Could not init Groq for Orchestrated Provider: {e}")

        if settings.GEMINI_API_KEY:
            try:
                self.gemini_provider = GeminiProvider()
            except Exception as e:
                logger.warning(f"Could not init Gemini for Orchestrated Provider: {e}")

    async def analyze_content(self, transcript: str, media_info: Dict[str, Any]) -> ContentAnalysisResult:
        # Prefer Gemini for holistic reasoning
        for prov in [self.gemini_provider, self.groq_provider, self.mock_provider]:
            if prov:
                try:
                    return await prov.analyze_content(transcript, media_info)
                except Exception as e:
                    logger.warning(f"{prov.__class__.__name__}.analyze_content failed in hybrid mode: {e}")
        return ContentAnalysisResult(summary="Video content analysis", main_topics=["Shorts"], tone="engaging")

    async def generate_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        requested_count: int,
        duration_target: str = "30-45s",
        mode: str = "podcast",
        custom_instructions: Optional[str] = None,
    ) -> List[RawCandidateMoment]:
        # Fast candidate discovery: Groq is champion for rapid extraction, fallback to Gemini, then Mock
        candidates_chain = [self.groq_provider, self.gemini_provider, self.mock_provider]
        for prov in candidates_chain:
            if prov:
                try:
                    logger.info(f"Hybrid Engine: Generating candidates using {prov.__class__.__name__}...")
                    cands = await prov.generate_candidates(
                        transcript_segments=transcript_segments,
                        media_info=media_info,
                        requested_count=requested_count,
                        duration_target=duration_target,
                        mode=mode,
                        custom_instructions=custom_instructions,
                    )
                    if cands and len(cands) > 0:
                        return cands
                except Exception as e:
                    logger.warning(f"{prov.__class__.__name__}.generate_candidates failed in hybrid: {e}")

        return await self.mock_provider.generate_candidates(
            transcript_segments=transcript_segments,
            media_info=media_info,
            requested_count=requested_count,
            duration_target=duration_target,
            mode=mode,
            custom_instructions=custom_instructions,
        )

    async def rank_candidates(
        self,
        candidates: List[RawCandidateMoment],
        transcript_context: str,
    ) -> List[RawCandidateMoment]:
        # Prefer Gemini for deep ranking
        for prov in [self.gemini_provider, self.groq_provider, self.mock_provider]:
            if prov:
                try:
                    return await prov.rank_candidates(candidates, transcript_context)
                except Exception:
                    pass
        return await self.mock_provider.rank_candidates(candidates, transcript_context)

    async def generate_metadata(
        self,
        clip_transcript: str,
        clip_context: Dict[str, Any],
    ) -> PlatformClipMetadata:
        # Prefer Gemini for creative nuance, platform hashtags, and single-para copy
        metadata_chain = [self.gemini_provider, self.groq_provider, self.mock_provider]
        for prov in metadata_chain:
            if prov:
                try:
                    logger.info(f"Hybrid Engine: Generating viral metadata using {prov.__class__.__name__}...")
                    meta = await prov.generate_metadata(clip_transcript, clip_context)
                    if meta:
                        return meta
                except Exception as e:
                    logger.warning(f"{prov.__class__.__name__}.generate_metadata failed in hybrid: {e}")

        return await self.mock_provider.generate_metadata(clip_transcript, clip_context)

    async def analyze_visual_context(self, frame_paths: List[str]) -> Dict[str, Any]:
        if self.gemini_provider:
            try:
                return await self.gemini_provider.analyze_visual_context(frame_paths)
            except Exception:
                pass
        return {"visual_engagement": 85.0, "face_detected": True}


def get_ai_provider(provider_name: Optional[str] = None) -> AIProvider:
    """
    Return an AI reasoning provider:
    - 'orchestrated' / 'hybrid': Best-of-breed (Groq for candidate speed + Gemini for reasoning/copywriting)
    - 'gemini': Gemini primary with fallback
    - 'groq': Groq primary with fallback
    - 'mock': Deterministic local engine
    """
    chosen = (provider_name or settings.AI_PROVIDER or "orchestrated").lower().strip()
    if chosen in ("orchestrated", "hybrid", "parallel"):
        return HybridOrchestratedAIProvider()
    if chosen == "mock":
        return MockAIProvider()
    return ResilientAIProvider(chosen)
