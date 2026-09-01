"""Unit tests for the 6 caption presets and keyword emphasis engine."""

from pathlib import Path
from app.services.media.captioner import CaptionGenerator


def test_caption_preset_configs_available():
    generator = CaptionGenerator()
    presets = ["bold_yellow", "clean_white", "podcast_box", "cinematic", "meme_impact", "cyber_neon"]
    for p in presets:
        assert p in generator.PRESET_CONFIGS
        cfg = generator.PRESET_CONFIGS[p]
        assert "font_name" in cfg
        assert "font_size" in cfg
        assert "primary_color" in cfg
        assert "secondary_color" in cfg


def test_keyword_emphasis_detection():
    generator = CaptionGenerator()
    assert generator.is_keyword_emphasis("$10,000") is True
    assert generator.is_keyword_emphasis("85%") is True
    assert generator.is_keyword_emphasis("100k") is True
    assert generator.is_keyword_emphasis("secret") is True
    assert generator.is_keyword_emphasis("insane") is True
    assert generator.is_keyword_emphasis("mistake") is True
    assert generator.is_keyword_emphasis("the") is False
    assert generator.is_keyword_emphasis("standard") is False


def test_ass_generation_with_presets(tmp_path: Path):
    generator = CaptionGenerator()
    segments = [
        {
            "start": 10.0,
            "end": 14.0,
            "text": "This 100k secret changed everything.",
            "words": [
                {"word": "This", "start": 10.0, "end": 10.5},
                {"word": "100k", "start": 10.5, "end": 11.2},
                {"word": "secret", "start": 11.2, "end": 12.0},
                {"word": "changed", "start": 12.0, "end": 13.0},
                {"word": "everything.", "start": 13.0, "end": 14.0},
            ],
        }
    ]

    out_file = tmp_path / "test_preset.ass"
    generator.generate_ass(segments, 10.0, 14.0, out_file, style="cyber_neon")
    assert out_file.exists()

    content = out_file.read_text(encoding="utf-8")
    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert "Dialogue:" in content
