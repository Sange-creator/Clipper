"""Tests for video mirroring, anti-copyright filters, zoom/pan framing, and hook snapping."""

import asyncio
import pytest
from app.services.pipeline.context_expansion import context_expansion_service
from app.services.pipeline.ranking import ranking_service
from app.services.ai.base import RawCandidateMoment


def test_snap_to_hook_strips_fillers_and_preserves_hook():
    """Verify snap_to_hook strips leading fillers and does not drag start time 3 seconds backwards."""
    segments = [
        {
            "start": 10.0,
            "end": 13.5,
            "text": "Yeah so basically welcome back guys.",
            "words": [
                {"word": "Yeah", "start": 10.0, "end": 10.3},
                {"word": "so", "start": 10.4, "end": 10.7},
                {"word": "basically", "start": 10.8, "end": 11.3},
                {"word": "welcome", "start": 11.4, "end": 12.0},
                {"word": "back", "start": 12.1, "end": 12.5},
            ]
        },
        {
            "start": 14.0,
            "end": 18.0,
            "text": "So um nobody ever told you why this happens.",
            "words": [
                {"word": "So", "start": 14.0, "end": 14.3},
                {"word": "um", "start": 14.4, "end": 14.7},
                {"word": "nobody", "start": 14.8, "end": 15.3},
                {"word": "ever", "start": 15.4, "end": 15.8},
                {"word": "told", "start": 15.9, "end": 16.2},
                {"word": "you", "start": 16.3, "end": 16.5},
            ]
        }
    ]

    # Target start is 14.0 (the second sentence)
    snapped = context_expansion_service.snap_to_hook(14.0, segments)
    # Must skip "So" (14.0) and "um" (14.4) to snap directly to "nobody" (14.8)
    assert snapped == 14.8, f"Expected 14.8, got {snapped}"

    # Must NEVER jump backwards to 10.0
    assert snapped >= 14.0, f"Snapped went backwards: {snapped}"


def test_ranking_service_custom_duration():
    """Verify ranking_service properly honors custom_min_duration and custom_max_duration."""
    cands = [
        (
            RawCandidateMoment(
                start=0.0,
                end=20.0,
                hook_score=90.0,
                retention_score=90.0,
                curiosity_score=90.0,
                emotion_score=90.0,
                story_score=90.0,
                payoff_score=90.0,
                shareability_score=90.0,
                novelty_score=90.0,
                quotability_score=90.0,
                visual_score=90.0,
                audio_score=90.0,
                platform_score=90.0,
                reason="20 second clip",
            ),
            90.0,
            0.0,
        ),
        (
            RawCandidateMoment(
                start=0.0,
                end=55.0,
                hook_score=90.0,
                retention_score=90.0,
                curiosity_score=90.0,
                emotion_score=90.0,
                story_score=90.0,
                payoff_score=90.0,
                shareability_score=90.0,
                novelty_score=90.0,
                quotability_score=90.0,
                visual_score=90.0,
                audio_score=90.0,
                platform_score=90.0,
                reason="55 second clip",
            ),
            90.0,
            0.0,
        ),
    ]

    # Custom duration: 50s to 60s
    results = ranking_service.rank_and_select(
        cands,
        target_count=2,
        duration_preset="custom",
        custom_min_duration=50.0,
        custom_max_duration=60.0,
    )
    # The 55s clip should rank #1 because 20s clip suffers large penalty for being under 50s
    assert results[0][0].reason == "55 second clip", "55s clip should be preferred for 50-60s custom range"
    assert results[0][3] == 1  # Rank 1


@pytest.mark.asyncio
async def test_render_clip_mirror_copyright_scale_pan(tmp_path):
    """End-to-end verification of FFmpeg rendering with mirror, anti_copyright, scale, and pan."""
    from app.services.media.renderer import VideoRenderer
    import subprocess

    renderer = VideoRenderer()
    src_video = tmp_path / "test_src.mp4"
    out_video = tmp_path / "test_out.mp4"

    # Generate a 2.0s 1920x1080 test video with audio tone
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2.0:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2.0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "48000",
        str(src_video)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Render with mirror, anti_copyright, scale 1.25, pan x=10, pan y=-5
    rendered_path = await renderer.render_clip(
        source_video_path=src_video,
        start_time=0.0,
        end_time=1.5,
        output_video_path=out_video,
        mirror_video=True,
        anti_copyright=True,
        video_scale=1.25,
        video_pan_x=10.0,
        video_pan_y=-5.0,
        framing_mode="crop_9_16",
        burn_captions=False,
    )

    assert rendered_path.exists(), "Rendered output file must exist"
    assert rendered_path.stat().st_size > 1000, "Rendered output file must not be empty"

    # Probe rendered dimensions
    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        str(out_video)
    ], capture_output=True, text=True, check=True)

    w, h = [int(x.strip()) for x in probe.stdout.strip().split(",")]
    assert w == 1080, f"Expected width 1080, got {w}"
    assert h == 1920, f"Expected height 1920, got {h}"

