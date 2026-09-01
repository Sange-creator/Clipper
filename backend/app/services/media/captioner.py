"""Config-driven caption generator with 6 presets, animated ASS formatting and keyword emphasis."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

EMPHASIS_PATTERNS = [
    r"^\$?\d+[\d,\.]*[%kKmMbB]?$",  # Numbers, percentages, currency (e.g. $10k, 80%, 100)
    r"\b(secret|never|always|huge|insane|crazy|truth|mistake|stop|proven|guaranteed|warning)\b",
]


class CaptionGenerator:
    """Generates styled animated ASS and standard SRT subtitle files with keyword emphasis."""

    # 6 Config-Driven Caption Presets
    PRESET_CONFIGS = {
        "bold_yellow": {
            "font_name": "Arial Black",
            "font_size": 48,
            "primary_color": "&H00FFFFFF&",    # White
            "secondary_color": "&H0000FFFF&",  # Yellow highlight
            "outline_color": "&H00000000&",    # Black
            "back_color": "&H80000000&",
            "border_style": 1,
            "outline": 5,
            "shadow": 3,
            "margin_v": 280,
            "uppercase": True,
        },
        "clean_white": {
            "font_name": "Arial",
            "font_size": 38,
            "primary_color": "&H00FFFFFF&",
            "secondary_color": "&H00E0E0E0&",
            "outline_color": "&H00000000&",
            "back_color": "&H60000000&",
            "border_style": 1,
            "outline": 3,
            "shadow": 1,
            "margin_v": 260,
            "uppercase": False,
        },
        "podcast_box": {
            "font_name": "Trebuchet MS",
            "font_size": 42,
            "primary_color": "&H00FFFFFF&",
            "secondary_color": "&H0000D4FF&",  # Gold highlight
            "outline_color": "&H00000000&",
            "back_color": "&HA0000000&",       # Opaque backing box
            "border_style": 3,                 # Opaque box
            "outline": 8,
            "shadow": 0,
            "margin_v": 290,
            "uppercase": False,
        },
        "cinematic": {
            "font_name": "Georgia",
            "font_size": 36,
            "primary_color": "&H00F0F0F0&",
            "secondary_color": "&H00D0D0D0&",
            "outline_color": "&H00000000&",
            "back_color": "&H40000000&",
            "border_style": 1,
            "outline": 2,
            "shadow": 2,
            "margin_v": 240,
            "uppercase": False,
        },
        "meme_impact": {
            "font_name": "Impact",
            "font_size": 52,
            "primary_color": "&H00FFFFFF&",
            "secondary_color": "&H0000FF00&",  # Lime green highlight
            "outline_color": "&H00000000&",
            "back_color": "&H80000000&",
            "border_style": 1,
            "outline": 6,
            "shadow": 4,
            "margin_v": 320,
            "uppercase": True,
        },
        "cyber_neon": {
            "font_name": "Arial Black",
            "font_size": 46,
            "primary_color": "&H00FFFF00&",    # Cyan
            "secondary_color": "&H00FF00FF&",  # Magenta
            "outline_color": "&H00000000&",
            "back_color": "&H80000000&",
            "border_style": 1,
            "outline": 6,
            "shadow": 4,
            "margin_v": 280,
            "uppercase": True,
        },
    }

    def format_timestamp_ass(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        if centisecs >= 100:
            secs += 1
            centisecs = 0
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def format_timestamp_srt(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int(round((seconds - int(seconds)) * 1000))
        if millisecs >= 1000:
            secs += 1
            millisecs = 0
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def is_keyword_emphasis(self, word: str) -> bool:
        """Check if a word matches high-impact keyword patterns (numbers, shock adjectives)."""
        clean = re.sub(r"[^\w$%]", "", word).lower()
        for pat in EMPHASIS_PATTERNS:
            if re.search(pat, clean, re.IGNORECASE):
                return True
        return False

    def generate_ass(
        self,
        segments: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        output_path: Path | str,
        style: str = "bold_yellow",
        subtitle_position: Optional[int] = 75,
    ) -> Path:
        """
        Generate an Advanced SubStation Alpha (.ass) subtitle file.
        All timestamps are relative to the sliced clip start (0.0s).
        subtitle_position: percentage height from top of screen (10% to 90%, default 75%).
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cfg = self.PRESET_CONFIGS.get(style, self.PRESET_CONFIGS["bold_yellow"])

        font_name = cfg["font_name"]
        font_size = cfg["font_size"]
        primary_color = cfg["primary_color"]
        secondary_color = cfg["secondary_color"]
        outline_color = cfg["outline_color"]
        back_color = cfg["back_color"]
        border_style = cfg["border_style"]
        outline = cfg["outline"]
        shadow = cfg["shadow"]
        uppercase = cfg["uppercase"]

        # Calculate MarginV based on screen percentage (10% = Top, 50% = Center, 75% = Lower-Third, 90% = Bottom)
        if subtitle_position is not None:
            # PlayResY is 1920. Alignment 2 measures from the bottom edge.
            pos_pct = max(10, min(90, subtitle_position))
            margin_v = max(60, min(1750, int(1920 * (1.0 - (pos_pct / 100.0)))))
        else:
            margin_v = cfg.get("margin_v", 320)

        ass_header = f"""[Script Info]
Title: AI Clipper Animated Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},{back_color},-1,0,0,0,100,100,1,0,{border_style},{outline},{shadow},2,60,60,{margin_v},1
Style: Emphasis,{font_name},{int(font_size * 1.1)},{secondary_color},{primary_color},{outline_color},{back_color},-1,0,0,0,110,110,1,0,{border_style},{outline + 1},{shadow + 1},2,60,60,{margin_v},1


[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        dialogue_lines: List[str] = []

        for seg in segments:
            seg_start = seg.get("start", 0.0)
            seg_end = seg.get("end", 0.0)
            words = seg.get("words", [])

            if seg_end <= clip_start or seg_start >= clip_end:
                continue

            rel_start = max(0.0, seg_start - clip_start)
            rel_end = max(0.1, min(clip_end - clip_start, seg_end - clip_start))

            if words and len(words) > 0:
                # 3-5 word chunks for short-form retention
                chunk_size = 4
                for c in range(0, len(words), chunk_size):
                    chunk = words[c : c + chunk_size]
                    c_start = max(0.0, chunk[0].get("start", seg_start) - clip_start)
                    c_end = max(0.1, min(clip_end - clip_start, chunk[-1].get("end", seg_end) - clip_start))
                    if c_start >= clip_end - clip_start or c_end <= 0:
                        continue

                    karaoke_parts = []
                    for w in chunk:
                        w_start = w.get("start", seg_start) - clip_start
                        w_end = w.get("end", seg_end) - clip_start
                        duration_cs = max(10, int((w_end - w_start) * 100))
                        word_str = w.get("word", "").strip()
                        if uppercase:
                            word_str = word_str.upper()

                        # Check keyword emphasis
                        if self.is_keyword_emphasis(word_str):
                            karaoke_parts.append(f"{{\\c{secondary_color}\\fscx110\\fscy110}}{{\\k{duration_cs}}}{word_str}{{\\r}}")
                        else:
                            karaoke_parts.append(f"{{\\k{duration_cs}}}{word_str}")

                    text_content = " ".join(karaoke_parts)
                    start_str = self.format_timestamp_ass(c_start)
                    end_str = self.format_timestamp_ass(c_end)
                    dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_content}")
            else:
                text = seg.get("text", "").strip()
                if uppercase:
                    text = text.upper()
                if text:
                    start_str = self.format_timestamp_ass(rel_start)
                    end_str = self.format_timestamp_ass(rel_end)
                    dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(dialogue_lines) + "\n")

        return out_file

    def generate_srt(
        self,
        segments: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        output_path: Path | str,
    ) -> Path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        srt_entries: List[str] = []
        counter = 1

        for seg in segments:
            seg_start = seg.get("start", 0.0)
            seg_end = seg.get("end", 0.0)
            if seg_end <= clip_start or seg_start >= clip_end:
                continue

            rel_start = max(0.0, seg_start - clip_start)
            rel_end = max(0.1, min(clip_end - clip_start, seg_end - clip_start))
            text = seg.get("text", "").strip()

            if text:
                srt_entries.append(
                    f"{counter}\n{self.format_timestamp_srt(rel_start)} --> {self.format_timestamp_srt(rel_end)}\n{text}\n"
                )
                counter += 1

        with open(out_file, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_entries))

        return out_file


captioner = CaptionGenerator()
