"""Tests for AI provider abstraction, mock provider, and factory fallback."""

import pytest
from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.ai.mock import MockAIProvider


@pytest.mark.asyncio
async def test_mock_ai_provider_generates_valid_candidates():
    provider = MockAIProvider()
    segments = [
        {"start": 0.0, "end": 5.0, "text": "What if everything you knew about content was wrong?"},
        {"start": 5.1, "end": 15.0, "text": "Most people create long boring videos with no hook."},
        {"start": 15.1, "end": 35.0, "text": "Here is the exact secret to hook viewers immediately."},
    ]
    candidates = await provider.generate_candidates(
        transcript_segments=segments,
        media_info={"duration_seconds": 40.0},
        requested_count=5,
        duration_target="30-45s",
    )
    assert len(candidates) >= 1
    first = candidates[0]
    assert first.hook_score > 0.0
    assert first.retention_score > 0.0
    assert first.payoff_score > 0.0
    assert first.start < first.end


@pytest.mark.asyncio
async def test_ai_provider_generates_metadata():
    provider = MockAIProvider()
    meta = await provider.generate_metadata(
        clip_transcript="Never make this huge mistake with your content.",
        clip_context={"hook_summary": "Never make this huge mistake"},
    )
    assert meta.tiktok_title
    assert meta.reels_caption
    assert meta.shorts_title
    assert len(meta.tiktok_hashtags) > 0


def test_factory_fallback_to_mock_when_no_keys():
    provider = get_ai_provider("mock")
    assert isinstance(provider, MockAIProvider)


@pytest.mark.asyncio
async def test_resilient_ai_provider_failover_on_error():
    provider = get_ai_provider("groq")
    segments = [
        {"start": 0.0, "end": 10.0, "text": "This is a test transcript segment for failover."},
        {"start": 10.1, "end": 25.0, "text": "Here is the key payoff moment."},
    ]
    # Even if Groq / Gemini fail or have invalid keys, ResilientAIProvider will return candidates
    candidates = await provider.generate_candidates(
        transcript_segments=segments,
        media_info={"duration_seconds": 30.0},
        requested_count=2,
        duration_target="15-30s",
    )
    assert len(candidates) >= 1
    assert candidates[0].hook_score > 0

