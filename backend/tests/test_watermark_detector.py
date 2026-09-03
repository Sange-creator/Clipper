"""Tests for automated watermark and logo detection using OpenCV."""

import pytest
from pathlib import Path
from app.services.media.watermark_detector import WatermarkDetector, WatermarkDetectionResult


@pytest.mark.asyncio
async def test_watermark_detector_initialization():
    detector = WatermarkDetector(sample_frames_count=10, edge_threshold=0.20)
    assert detector.sample_frames_count == 10
    assert detector.edge_threshold == 0.20


@pytest.mark.asyncio
async def test_watermark_detector_missing_file():
    detector = WatermarkDetector()
    result = await detector.detect_watermark("/path/to/nonexistent/video.mp4")
    assert isinstance(result, WatermarkDetectionResult)
    assert result.detected is False
    assert result.position == "none"
    assert result.confidence == 0.0
    assert result.delogo_filter == ""


def test_score_roi_watermark_flat_frames():
    import numpy as np
    detector = WatermarkDetector()
    # 5 blank black frames (no watermark edges)
    frames = [np.zeros((60, 100), dtype=np.uint8) for _ in range(5)]
    score = detector._score_roi_watermark(frames)
    assert score < 0.20
