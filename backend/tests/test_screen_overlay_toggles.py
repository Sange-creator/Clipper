import pytest
from pathlib import Path
from app.services.media.captioner import captioner


def test_independent_overlay_toggles_ass(tmp_path: Path):
    segments = [
        {
            "start": 0.0,
            "end": 4.0,
            "text": "Check out this wild event that happened.",
            "words": [
                {"word": "Check", "start": 0.0, "end": 0.5},
                {"word": "out", "start": 0.5, "end": 0.9},
                {"word": "this", "start": 0.9, "end": 1.4},
                {"word": "wild", "start": 1.4, "end": 2.0},
                {"word": "event", "start": 2.0, "end": 2.8},
                {"word": "that", "start": 2.8, "end": 3.2},
                {"word": "happened", "start": 3.2, "end": 4.0},
            ],
        }
    ]

    # 1. All three ON (subtitles + part badge + hook header)
    all_on_file = tmp_path / "all_on.ass"
    captioner.generate_ass(
        segments=segments,
        clip_start=0.0,
        clip_end=4.0,
        output_path=all_on_file,
        style="tiktok_viral",
        add_hook_header=True,
        hook_header_text="POLICE CHASE SUSPECT",
        part_index=1,
        total_parts=5,
        add_part_badge=True,
        show_subtitles=True,
    )
    all_on_content = all_on_file.read_text()
    assert "Dialogue: 2," in all_on_content  # PartBadge
    assert "PART 1" in all_on_content
    assert "Dialogue: 1," in all_on_content  # HookHeader
    assert "POLICE CHASE SUSPECT" in all_on_content
    assert "Dialogue: 0," in all_on_content  # Karaoke subtitles

    # 2. Subtitles OFF, Part Badge ON, Hook Header ON
    no_sub_file = tmp_path / "no_sub.ass"
    captioner.generate_ass(
        segments=segments,
        clip_start=0.0,
        clip_end=4.0,
        output_path=no_sub_file,
        style="tiktok_viral",
        add_hook_header=True,
        hook_header_text="POLICE CHASE SUSPECT",
        part_index=2,
        total_parts=5,
        add_part_badge=True,
        show_subtitles=False,  # Subtitles OFF
    )
    no_sub_content = no_sub_file.read_text()
    assert "Dialogue: 2," in no_sub_content  # PartBadge
    assert "PART 2" in no_sub_content
    assert "Dialogue: 1," in no_sub_content  # HookHeader
    assert "Dialogue: 0," not in no_sub_content  # NO spoken subtitles!

    # 3. Part Badge OFF, Subtitles ON, Hook Header ON
    no_part_file = tmp_path / "no_part.ass"
    captioner.generate_ass(
        segments=segments,
        clip_start=0.0,
        clip_end=4.0,
        output_path=no_part_file,
        style="tiktok_viral",
        add_hook_header=True,
        hook_header_text="POLICE CHASE SUSPECT",
        part_index=3,
        total_parts=5,
        add_part_badge=False,  # Part Badge OFF
        show_subtitles=True,
    )
    no_part_content = no_part_file.read_text()
    assert "Dialogue: 2," not in no_part_content  # NO PartBadge!
    assert "PART 3" not in no_part_content
    assert "Dialogue: 1," in no_part_content  # HookHeader
    assert "Dialogue: 0," in no_part_content  # Spoken subtitles

    # 4. Hook Header OFF (even when total_parts > 1), Subtitles ON, Part Badge ON
    no_hook_file = tmp_path / "no_hook.ass"
    captioner.generate_ass(
        segments=segments,
        clip_start=0.0,
        clip_end=4.0,
        output_path=no_hook_file,
        style="tiktok_viral",
        add_hook_header=False,  # Hook Header OFF
        hook_header_text="POLICE CHASE SUSPECT",
        part_index=4,
        total_parts=5,
        add_part_badge=True,
        show_subtitles=True,
    )
    no_hook_content = no_hook_file.read_text()
    assert "Dialogue: 1," not in no_hook_content  # NO HookHeader!
    assert "POLICE CHASE SUSPECT" not in no_hook_content
    assert "Dialogue: 2," in no_hook_content  # PartBadge present
    assert "PART 4" in no_hook_content
    assert "Dialogue: 0," in no_hook_content  # Spoken subtitles present

    # 5. ALL THREE OFF (clean video mode)
    all_off_file = tmp_path / "all_off.ass"
    captioner.generate_ass(
        segments=segments,
        clip_start=0.0,
        clip_end=4.0,
        output_path=all_off_file,
        style="tiktok_viral",
        add_hook_header=False,  # Hook Header OFF
        hook_header_text="POLICE CHASE SUSPECT",
        part_index=5,
        total_parts=5,
        add_part_badge=False,  # Part Badge OFF
        show_subtitles=False,  # Subtitles OFF
    )
    all_off_content = all_off_file.read_text()
    # Entire events section should contain 0 Dialogue lines
    assert "Dialogue:" not in all_off_content
