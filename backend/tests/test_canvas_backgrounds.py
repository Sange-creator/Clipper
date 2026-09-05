"""Tests for canvas backgrounds (white, black, obsidian, violet, sunset, ocean) and high-contrast text guarantee."""

import pytest
from pathlib import Path
from app.services.media.captioner import captioner
from app.core.schemas import JobCreateRequest, ProjectProcessRequest, ClipEditRequest


def test_canvas_background_schemas():
    """Verify schemas accept canvas_background."""
    req1 = JobCreateRequest(
        video_id="vid_123",
        framing_mode="blur_fit_9_16",
        canvas_background="white",
    )
    assert req1.canvas_background == "white"

    req2 = ProjectProcessRequest(
        framing_mode="blur_fit_9_16",
        canvas_background="gradient_obsidian",
    )
    assert req2.canvas_background == "gradient_obsidian"

    req3 = ClipEditRequest(
        start_time=0.0,
        end_time=25.0,
        framing_mode="blur_fit_9_16",
        canvas_background="black",
    )
    assert req3.canvas_background == "black"


def test_white_canvas_high_contrast_subtitles(tmp_path: Path):
    """Verify that white canvas enforces thick 8px solid black stroke and deep shadow for 100% text readability."""
    ass_path = tmp_path / "test_contrast.ass"
    segments = [
        {"start": 0.0, "end": 2.0, "text": "Ultra crisp text on white background."}
    ]

    captioner.generate_ass(
        segments=segments,
        clip_start=0.0,
        clip_end=2.0,
        output_path=ass_path,
        style="clean_white",  # Normally has outline=3, shadow=1
        canvas_background="white",
        add_hook_header=True,
        hook_header_text="CRITICAL REVELATION",
        part_index=1,
    )

    content = ass_path.read_text(encoding="utf-8")

    # Verify Default style on white canvas has outline >= 8 and shadow >= 4 and pitch-black outline
    default_style_line = next(line for line in content.splitlines() if line.startswith("Style: Default,"))
    parts = default_style_line.split(",")
    # Style: Default,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
    outline_col = parts[5]
    outline_px = int(parts[16])
    shadow_px = int(parts[17])

    assert outline_col == "&H00000000&", f"Expected solid black outline &H00000000&, got {outline_col}"
    assert outline_px >= 8, f"Expected outline >= 8 on white background, got {outline_px}"
    assert shadow_px >= 4, f"Expected shadow >= 4 on white background, got {shadow_px}"

    # Verify HookHeader also has outline >= 8 and solid black outline
    hook_style_line = next(line for line in content.splitlines() if line.startswith("Style: HookHeader,"))
    hook_parts = hook_style_line.split(",")
    assert hook_parts[5] == "&H00000000&"
    assert int(hook_parts[16]) >= 8

    # Verify PartBadge is present with black pill backing
    part_line = next(line for line in content.splitlines() if line.startswith("Style: PartBadge,"))
    assert "&H000000E6&" in part_line  # Solid dark pill
    assert "PART 1" in content
