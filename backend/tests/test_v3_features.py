"""Tests for V3 Backlog Features: Silence Detection, Timeline Cuts, Subtitle Toggling, and Mode Discovery."""

import pytest
from pathlib import Path
from app.services.media.silence_detector import SilenceDetector, SilenceInterval, TimelineEdit
from app.services.media.renderer import retime_ass_subtitles
from app.services.ai.prompt_templates import get_discovery_prompt, PODCAST_DISCOVERY_SYSTEM_PROMPT, VIRAL_MOMENTS_DISCOVERY_SYSTEM_PROMPT
from app.services.ai.mock import MockAIProvider


def test_silence_detector_timeline_cuts():
    """Test dead-air interval removal and kept segments generation."""
    detector = SilenceDetector()

    # Simulate silences: one long 3.0s dead air interval between 12.0s and 15.0s
    silences = [
        SilenceInterval(start=12.0, end=15.0, duration=3.0),
        SilenceInterval(start=28.0, end=28.4, duration=0.4), # short natural pause, should NOT be cut
    ]

    edit = detector.build_edited_timeline(
        start_time=0.0,
        end_time=30.0,
        silence_intervals=silences,
        dead_air_threshold_sec=1.2,
    )

    assert isinstance(edit, TimelineEdit)
    assert edit.source_start == 0.0
    assert edit.source_end == 30.0
    assert len(edit.keep) == 2
    # Kept slice 1 starts at 0.0 and ends around 12.15s
    assert edit.keep[0][0] == 0.0
    assert edit.keep[0][1] <= 12.2
    # Kept slice 2 starts around 14.85s and ends at 30.0s
    assert edit.keep[1][0] >= 14.8
    assert edit.keep[1][1] == 30.0
    assert edit.dead_air_removed_seconds > 2.0


def test_retime_ass_subtitles():
    """Test re-timing of ASS subtitle dialog lines when dead air is cut."""
    ass_sample = """[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:02.00,0:00:05.00,Default,,0,0,0,,First sentence
Dialogue: 0,0:00:16.00,0:00:20.00,Default,,0,0,0,,Second sentence after cut
"""
    # Suppose we kept [0.0, 10.0] and [15.0, 25.0] (5.0s dead air cut between 10s and 15s)
    kept = [[0.0, 10.0], [15.0, 25.0]]
    retimed = retime_ass_subtitles(ass_sample, kept)

    # First sentence (2s -> 5s) stays 0:00:02.00 -> 0:00:05.00
    assert "0:00:02.00,0:00:05.00" in retimed
    # Second sentence (orig 16s -> 20s) should now be shifted by -5s: (11s -> 15s)
    assert "0:00:11.00,0:00:15.00" in retimed


def test_v3_prompt_generation_for_modes():
    """Test dedicated system prompts for Podcast vs Viral Moments."""
    podcast_prompt = get_discovery_prompt("podcast", "30-45s", 50)
    assert "Regular Podcast Clipper" in podcast_prompt
    assert "30-45s" in podcast_prompt

    viral_prompt = get_discovery_prompt("viral_moments", "45-60s", 60)
    assert "Long Video Viral Moment Clipper" in viral_prompt
    assert "45-60s" in viral_prompt


@pytest.mark.asyncio
async def test_mock_ai_provider_modes_and_v3_scores():
    """Test that MockAIProvider respects mode and generates 14-factor V3 scores."""
    mock_ai = MockAIProvider()
    segments = [
        {"start": 0.0, "end": 10.0, "text": "What if I told you the secret to growth?"},
        {"start": 10.0, "end": 20.0, "text": "Most people think it is complicated."},
        {"start": 20.0, "end": 35.0, "text": "In conclusion, simplicity always wins."},
    ]

    candidates = await mock_ai.generate_candidates(
        transcript_segments=segments,
        media_info={"duration_seconds": 35.0},
        requested_count=2,
        duration_target="15-30s",
        mode="viral_moments",
    )

    assert len(candidates) >= 1
    cand = candidates[0]
    assert cand.standalone_score > 0
    assert cand.rewatch_score > 0
    assert "viral_moments" in cand.reason
