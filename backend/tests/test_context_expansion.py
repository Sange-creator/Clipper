"""Tests for context expansion and boundary snapping."""

import pytest
from app.services.ai.base import RawCandidateMoment
from app.services.pipeline.context_expansion import ContextExpansionService


def test_filler_word_removal():
    svc = ContextExpansionService()
    segments = [
        {
            "start": 10.0,
            "end": 14.0,
            "text": "So basically here is the trick",
            "words": [
                {"word": "So", "start": 10.0, "end": 10.4},
                {"word": "basically", "start": 10.5, "end": 11.2},
                {"word": "here", "start": 11.3, "end": 11.8},
                {"word": "is", "start": 11.9, "end": 12.1},
                {"word": "the", "start": 12.2, "end": 12.4},
                {"word": "trick", "start": 12.5, "end": 13.0},
            ]
        },
        {
            "start": 14.1,
            "end": 35.0,
            "text": "you need to focus on retention.",
            "words": [
                {"word": "you", "start": 14.1, "end": 14.5},
                {"word": "need", "start": 14.6, "end": 15.0},
                {"word": "to", "start": 15.1, "end": 15.3},
                {"word": "focus", "start": 15.4, "end": 16.0},
                {"word": "on", "start": 16.1, "end": 16.3},
                {"word": "retention.", "start": 16.4, "end": 17.0},
            ]
        }
    ]

    cand = RawCandidateMoment(start=10.0, end=35.0, hook_score=85.0)
    expanded = svc.expand_candidate_context(cand, segments, video_duration=60.0)
    # The filler word "So" should be skipped, snapping start to 10.5 or first meaningful word
    assert expanded.start >= 10.5
    assert expanded.end == 35.0
