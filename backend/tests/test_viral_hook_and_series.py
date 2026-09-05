"""Tests for intense 10-second hook scoring, multi-genre candidate discovery,
multi-part series subtitles, TikTok rounded box captions, and single-paragraph copy-paste.
"""

import pytest
from pathlib import Path
from app.services.media.audio_analyzer import (
    AudioScriptAnalyzer,
    build_single_para_post,
    strip_emojis,
)
from app.services.media.captioner import CaptionService
from app.services.ai.prompt_templates import get_discovery_prompt, GENRE_DIRECTIVES


def test_genre_directives_and_hook_prompts():
    """Verify that all genres are configured and include first 10-second hook directives."""
    genres = ["action_chase_pov", "military_history", "nostalgia", "vlog_pov", "podcast_debate", "viral_moments"]
    for g in genres:
        assert g in GENRE_DIRECTIVES
        prompt = get_discovery_prompt("viral_moments", "30-45s", 40, video_title="Epic Police Chase", genre=g)
        assert "MANDATORY FIRST 10 SECONDS HOOK RULE" in prompt
        assert "Epic Police Chase" in prompt
        assert "climax_start" in prompt


def test_audio_script_analyzer_hook_penalties_and_boosts():
    """Verify that calm greetings receive heavy penalties and chaos/fights receive strong boosts."""
    analyzer = AudioScriptAnalyzer()

    # Calm greeting intro: Should receive penalty
    calm_text = "Hey guys, welcome back to the channel. Today we have a quick update for you."
    score_calm, _ = analyzer.score_opening_hook(calm_text, word_count=len(calm_text.split()))
    assert score_calm <= 65.0

    # Chaos / fight / police chase intro: Should score high (85+)
    chaos_text = "Suspect is running! Shots fired, stop right now or I will tackle you!"
    score_chaos, _ = analyzer.score_opening_hook(chaos_text, word_count=len(chaos_text.split()))
    assert score_chaos >= 85.0

    # Military history intro
    history_text = "In 1944, this secret weapon was deployed and wiped out the entire division."
    score_hist, _ = analyzer.score_opening_hook(history_text, word_count=len(history_text.split()), genre="military_history")
    assert score_hist >= 80.0


def test_tiktok_rounded_box_caption_preset(tmp_path):
    """Test generating subtitles with the tiktok_rounded_box (rounded translucent pill) preset."""
    captioner = CaptionService()
    ass_file = tmp_path / "test_pill.ass"

    segments = [
        {
            "start": 0.0,
            "end": 3.0,
            "text": "Get down on the ground right now!",
            "words": [
                {"word": "Get", "start": 0.0, "end": 0.5},
                {"word": "down", "start": 0.5, "end": 1.0},
                {"word": "on", "start": 1.0, "end": 1.5},
                {"word": "the", "start": 1.5, "end": 2.0},
                {"word": "ground", "start": 2.0, "end": 3.0},
            ]
        }
    ]

    captioner.generate_ass(
        segments,
        0.0,
        3.0,
        ass_file,
        style="tiktok_rounded_box",
        add_hook_header=True,
        hook_header_text="INSANE POLICE CHASE",
        part_index=1,
        total_parts=5,
    )

    assert ass_file.exists()
    assert captioner.get_preset_config("tiktok_rounded_box")["border_style"] == 3
    assert captioner.get_preset_config("tiktok_pill")["border_style"] == 3

    content = ass_file.read_text(encoding="utf-8")
    # Must use rounded pill styling (border style 3 with padding)
    assert ",3,10,0," in content
    # Header must include Part 1 (strictly no /5) and hook title
    assert "PART 1" in content
    assert "PART 1/" not in content
    assert "INSANE POLICE CHASE" in content
    assert "HookHeader" in content


def test_single_para_builder():
    """Test building a 1-click single-paragraph copy-paste block."""
    single = build_single_para_post(
        title="SUSPECT CORNERED IN ALLEY",
        caption="Officer bodycam captures the exact moment the suspect made a run for it.",
        hashtags=["#policepov", "#bodycam", "#viral", "#chase", "#shorts"],
        part_index=2,
        total_parts=5,
    )

    assert single.startswith("Part 2/5: SUSPECT CORNERED IN ALLEY")
    assert "Officer bodycam captures" in single
    assert "#policepov" in single
    assert "\n" not in single  # Must be a single contiguous paragraph
