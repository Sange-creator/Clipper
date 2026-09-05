"""Config-driven caption generator with captivating TikTok creator styling, animated ASS formatting, keyword emphasis, and persistent hook headers."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

EMPHASIS_PATTERNS = [
    r"^\$?\d+[\d,\.]*[%kKmMbB]?$",  # Numbers, percentages, currency (e.g. $10k, 80%, 100)
    r"\b(secret|never|always|huge|insane|crazy|truth|mistake|stop|proven|guaranteed|warning|shocking|unbelievable|wtf|omg|must|crucial)\b",
]

# Contextual Creator Emojis for TikTok / Reels / Shorts
EMOJI_KEYWORDS = {
    "shock": ["🤯", "😱", "😳", "👀"],
    "warning": ["⚠️", "🛑", "❌", "🚨"],
    "money": ["💰", "💵", "🤑", "📈"],
    "fire": ["🔥", "⚡️", "💥", "🚀"],
    "secret": ["🤫", "🔒", "🔑", "👀"],
    "humor": ["💀", "😂", "🤣", "😭"],
    "top": ["💯", "👑", "🎯", "✨"],
}

DEFAULT_VIRAL_EMOJIS = ["🤯", "🔥", "😱", "💀", "🤫", "❌", "💯", "⚠️", "🚀", "👀"]


from app.services.media.audio_analyzer import strip_emojis


def format_tiktok_hook_header(hook_text: str, custom_text: Optional[str] = None) -> str:
    """
    Format text into a high-CTR, punchy TikTok creator hook header:
    - Clean uppercase phrasing
    - Auto-wraps onto 2 balanced lines using \\N if long (> 28 chars)
    - Strips all Unicode emojis to guarantee no missing character tofu boxes (□) in FFmpeg libass
    """
    raw = (custom_text or hook_text or "").strip()
    if not raw:
        return "WAIT TILL THE END"

    # Strip emojis to avoid font tofu boxes (□)
    cleaned = strip_emojis(raw).strip()
    # Remove outer quotes and redundant punctuation
    cleaned = re.sub(r"^[\"']|[\"']$", "", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = "MUST WATCH"

    # Auto-wrap cleanly onto 2 lines with \N if long (> 28 chars)
    if len(cleaned) > 28 and " " in cleaned:
        words = cleaned.split(" ")
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        return f"{line1.upper()}\\N{line2.upper()}"

    return cleaned.upper()


class CaptionGenerator:
    """Generates styled animated ASS and standard SRT subtitle files with keyword emphasis and persistent hook titles."""

    # 8 Config-Driven Caption Presets
    PRESET_CONFIGS = {
        "tiktok_viral": {
            "font_name": "Arial Black",
            "font_size": 48,
            "primary_color": "&H00FFFFFF&",    # Crisp White
            "secondary_color": "&H0000FFFF&",  # Electric Neon Yellow highlight
            "outline_color": "&H00000000&",    # Solid Black
            "back_color": "&H90000000&",
            "border_style": 1,
            "outline": 6,
            "shadow": 3,
            "margin_v": 280,
            "uppercase": True,
        },
        "hormozi_bold": {
            "font_name": "Impact",
            "font_size": 52,
            "primary_color": "&H00FFFFFF&",    # White
            "secondary_color": "&H0000FF00&",  # High-impact Neon Lime Green
            "outline_color": "&H00000000&",
            "back_color": "&HA0000000&",
            "border_style": 1,
            "outline": 7,
            "shadow": 4,
            "margin_v": 300,
            "uppercase": True,
        },
        "meme": {
            "font_name": "Impact",
            "font_size": 54,
            "primary_color": "&H00FFFFFF&",    # Solid Crisp White
            "secondary_color": "&H0000FFFF&",  # Meme Yellow Punch
            "outline_color": "&H00000000&",    # Extra Heavy Black Stroke
            "back_color": "&HA0000000&",
            "border_style": 1,
            "outline": 8,
            "shadow": 4,
            "margin_v": 320,
            "uppercase": True,
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
        "nostalgic": {
            "font_name": "Courier New",
            "font_size": 44,
            "primary_color": "&H00C8ECF8&",    # Warm Vintage Cream / Amber
            "secondary_color": "&H0020C0FF&",  # Warm Sunset Amber Gold highlight
            "outline_color": "&H00142030&",    # Burnt Sepia / Espresso outline
            "back_color": "&H80001020&",
            "border_style": 1,
            "outline": 5,
            "shadow": 3,
            "margin_v": 280,
            "uppercase": False,
        },
        "old_history": {
            "font_name": "Georgia",
            "font_size": 42,
            "primary_color": "&H00D8F0F8&",    # Parchment Ivory
            "secondary_color": "&H0048B8D8&",  # Antique Gold / Historical Bronze
            "outline_color": "&H00101824&",    # Deep Sepia Slate
            "back_color": "&H90101824&",
            "border_style": 1,
            "outline": 4,
            "shadow": 3,
            "margin_v": 260,
            "uppercase": False,
        },
        "white_background": {
            "font_name": "Arial Black",
            "font_size": 44,
            "primary_color": "&H00000000&",    # Deep Pitch Black Text
            "secondary_color": "&H000020D8&",  # Crimson Red Accent
            "outline_color": "&H00FFFFFF&",    # Matching White Border
            "back_color": "&H00FFFFFF&",       # Pure Solid White Box
            "border_style": 3,                 # Solid Bounding Box
            "outline": 10,
            "shadow": 0,
            "margin_v": 280,
            "uppercase": True,
        },
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
            "font_size": 38,
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
        "playful_comic": {
            "font_name": "Comic Sans MS",
            "font_size": 44,
            "primary_color": "&H00FFFFFF&",
            "secondary_color": "&H00FF20A0&",  # Bubblegum Pink
            "outline_color": "&H00000000&",
            "back_color": "&H80000000&",
            "border_style": 1,
            "outline": 5,
            "shadow": 3,
            "margin_v": 280,
            "uppercase": False,
        },
        "editorial_serif": {
            "font_name": "Times New Roman",
            "font_size": 42,
            "primary_color": "&H00F5F5F5&",
            "secondary_color": "&H0000D4FF&",  # Luxury Gold
            "outline_color": "&H00000000&",
            "back_color": "&H60000000&",
            "border_style": 1,
            "outline": 3,
            "shadow": 2,
            "margin_v": 260,
            "uppercase": False,
        },
        "capcut_black_box": {
            "font_name": "Arial Black",
            "font_size": 48,
            "primary_color": "&H00FFFFFF&",    # Crisp White
            "secondary_color": "&H0000FFFF&",  # Electric Neon Yellow highlight
            "outline_color": "&H00000000&",
            "back_color": "&HE6000000&",       # Opaque CapCut Black Box
            "border_style": 3,                 # Solid background bounding box
            "outline": 9,                      # Box padding
            "shadow": 0,
            "margin_v": 280,
            "uppercase": True,
        },
        "capcut_yellow_box": {
            "font_name": "Impact",
            "font_size": 48,
            "primary_color": "&H00000000&",    # Deep Black
            "secondary_color": "&H00FFFFFF&",  # White Accent
            "outline_color": "&H00000000&",
            "back_color": "&H0000E5FF&",       # CapCut Vibrant Yellow Box
            "border_style": 3,                 # Solid background bounding box
            "outline": 9,
            "shadow": 0,
            "margin_v": 280,
            "uppercase": True,
        },
        "tiktok_boxed": {
            "font_name": "Arial Black",
            "font_size": 50,
            "primary_color": "&H00FFFFFF&",    # Pure White
            "secondary_color": "&H0000FF00&",  # Neon Lime Green
            "outline_color": "&H00000000&",
            "back_color": "&HD9141414&",       # Opaque Dark Charcoal Box
            "border_style": 3,
            "outline": 10,
            "shadow": 0,
            "margin_v": 280,
            "uppercase": True,
        },
        "tiktok_rounded_box": {
            "font_name": "Arial Black",
            "font_size": 48,
            "primary_color": "&H00FFFFFF&",    # Crisp White
            "secondary_color": "&H0000FFFF&",  # Electric Neon Yellow highlight
            "outline_color": "&H00000000&",
            "back_color": "&HC0101010&",       # Translucent Rounded Charcoal Pill Box
            "border_style": 3,                 # Solid background bounding box
            "outline": 10,                     # Generous pill box padding
            "shadow": 0,
            "margin_v": 280,
            "uppercase": True,
        },
        "capcut_black_pill": {
            "font_name": "Arial Black",
            "font_size": 48,
            "primary_color": "&H00FFFFFF&",    # Crisp White
            "secondary_color": "&H0000FF00&",  # Neon Lime Green highlight
            "outline_color": "&H00000000&",
            "back_color": "&HE6080808&",       # Solid Deep Black Pill Box
            "border_style": 3,
            "outline": 11,
            "shadow": 0,
            "margin_v": 280,
            "uppercase": True,
        },
    }

    # Hook Header Visual Styles
    HOOK_HEADER_STYLES = {
        "viral_creator": {
            "font_name": "Arial Black",
            "font_size": 46,
            "primary_color": "&H0000FFFF&",    # Electric Neon Yellow
            "secondary_color": "&H00FFFFFF&",  # White
            "outline_color": "&H00000000&",    # Black
            "back_color": "&HA0000000&",
            "border_style": 1,
            "outline": 6,
            "shadow": 3,
        },
        "white_box": {
            "font_name": "Arial Black",
            "font_size": 42,
            "primary_color": "&H00000000&",    # Deep Black
            "secondary_color": "&H000000E0&",  # Crimson Accent
            "outline_color": "&H00FFFFFF&",    # White
            "back_color": "&H00FFFFFF&",       # Solid Pure White Box
            "border_style": 3,
            "outline": 9,
            "shadow": 0,
        },
        "white_background": {
            "font_name": "Arial Black",
            "font_size": 42,
            "primary_color": "&H00000000&",
            "secondary_color": "&H000000E0&",
            "outline_color": "&H00FFFFFF&",
            "back_color": "&H00FFFFFF&",
            "border_style": 3,
            "outline": 9,
            "shadow": 0,
        },
        "meme": {
            "font_name": "Impact",
            "font_size": 50,
            "primary_color": "&H00FFFFFF&",    # Crisp White
            "secondary_color": "&H0000FFFF&",  # Yellow
            "outline_color": "&H00000000&",    # Heavy Black
            "back_color": "&HB0000000&",
            "border_style": 1,
            "outline": 8,
            "shadow": 4,
        },
        "nostalgic": {
            "font_name": "Courier New",
            "font_size": 42,
            "primary_color": "&H0020D0FF&",    # Warm Vintage Amber
            "secondary_color": "&H00FFFFFF&",  # White
            "outline_color": "&H00102030&",    # Warm Sepia
            "back_color": "&H90001020&",
            "border_style": 1,
            "outline": 4,
            "shadow": 3,
        },
        "old_history": {
            "font_name": "Georgia",
            "font_size": 42,
            "primary_color": "&H00E0F0FA&",    # Parchment Ivory
            "secondary_color": "&H0050B0D8&",  # Antique Gold
            "outline_color": "&H00141C28&",    # Dark Slate
            "back_color": "&H90101824&",
            "border_style": 1,
            "outline": 3,
            "shadow": 3,
        },
        "neon_cyber": {
            "font_name": "Arial Black",
            "font_size": 44,
            "primary_color": "&H00FFFF00&",    # Electric Cyan
            "secondary_color": "&H00FF00FF&",  # Magenta
            "outline_color": "&H00000000&",
            "back_color": "&H80000000&",
            "border_style": 1,
            "outline": 6,
            "shadow": 4,
        },
    }

    def get_preset_config(self, style: str) -> Dict[str, Any]:
        """Resolve caption preset configuration with normalized alias matching."""
        raw = (style or "").lower().strip()
        alias_map = {
            "meme_classic": "meme",
            "meme_bold": "meme",
            "white_box": "white_background",
            "white_card": "white_background",
            "vintage": "nostalgic",
            "nostalgic_vintage": "nostalgic",
            "history": "old_history",
            "history_documentary": "old_history",
            "comic": "playful_comic",
            "editorial": "editorial_serif",
            "luxury": "editorial_serif",
            "tiktok_rounded": "tiktok_rounded_box",
            "rounded_box": "tiktok_rounded_box",
            "tiktok_pill": "tiktok_rounded_box",
            "rounded_pill": "tiktok_rounded_box",
            "black_pill": "capcut_black_pill",
        }
        key = alias_map.get(raw, raw)
        return self.PRESET_CONFIGS.get(key, self.PRESET_CONFIGS["bold_yellow"])

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
        add_hook_header: bool = False,
        hook_header_text: Optional[str] = None,
        hook_header_position: Optional[int] = 12,
        hook_header_style: Optional[str] = None,
        keep_intervals: Optional[List[List[float]]] = None,
        part_index: Optional[int] = None,
        total_parts: Optional[int] = None,
    ) -> Path:
        """
        Generate an Advanced SubStation Alpha (.ass) subtitle file.
        All timestamps are relative to the sliced clip start (0.0s).
        Supports multi-interval splicing (e.g. 5s climax teaser followed by narrative build-up)
        and multi-part series branding (e.g. PART 1/5 • TITLE).
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cfg = self.get_preset_config(style)

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
            sub_pos_pct = max(10, min(90, subtitle_position))
            margin_v = max(60, min(1750, int(1920 * (1.0 - (sub_pos_pct / 100.0)))))
        else:
            margin_v = cfg.get("margin_v", 320)

        # Calculate Hook Header MarginV (default 12% from top -> margin_v ~ 1689 from bottom)
        hook_pos_pct = max(8, min(90, hook_header_position if hook_header_position is not None else 12))
        hook_margin_v = max(60, min(1780, int(1920 * (1.0 - (hook_pos_pct / 100.0)))))

        # Resolve Hook Header style (explicit or inherit from matching caption style if available)
        resolved_hook_key = hook_header_style or (style if style in self.HOOK_HEADER_STYLES else "viral_creator")
        hook_cfg = self.HOOK_HEADER_STYLES.get(resolved_hook_key, self.HOOK_HEADER_STYLES["viral_creator"])
        hook_font = hook_cfg["font_name"]
        hook_size = hook_cfg["font_size"]
        hook_primary = hook_cfg["primary_color"]
        hook_secondary = hook_cfg["secondary_color"]
        hook_outline = hook_cfg["outline_color"]
        hook_back = hook_cfg["back_color"]
        hook_border = hook_cfg.get("border_style", 1)
        hook_out_px = hook_cfg.get("outline", 6)
        hook_shadow_px = hook_cfg.get("shadow", 3)

        ass_header = f"""[Script Info]
Title: AI Clipper Animated Captions & TikTok Hook
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
Style: PartBadge,Arial Black,36,&H00FFFFFF&,&H0000FFFF&,&H00000000&,&H000000E6&,-1,0,0,0,100,100,1,0,3,9,0,8,40,40,75,1
Style: HookHeader,{hook_font},{hook_size},{hook_primary},{hook_secondary},{hook_outline},{hook_back},-1,0,0,0,100,100,1,0,{hook_border},{hook_out_px},{hook_shadow_px},8,50,50,{max(140, hook_margin_v)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        intervals = keep_intervals or [[clip_start, clip_end]]
        total_duration = sum(max(0.0, e - s) for s, e in intervals)
        dialogue_lines: List[str] = []

        # 1. Add dedicated on-screen Part Badge on Layer 2 (e.g. "PART 1" or "PART 2")
        if part_index:
            part_str = f"PART {part_index}"
            start_str = self.format_timestamp_ass(0.0)
            end_str = self.format_timestamp_ass(max(0.5, total_duration))
            dialogue_lines.append(
                f"Dialogue: 2,{start_str},{end_str},PartBadge,,0,0,0,,{part_str}"
            )

        # 2. Add dedicated on-screen Hook Title on Layer 1 (analyzed from audio script)
        should_render_hook = (add_hook_header or (total_parts and total_parts > 1)) and hook_header_text
        if should_render_hook:
            # If multi-interval teaser is active (first interval is 3-8s teaser):
            if len(intervals) > 1 and intervals[0] != intervals[-1]:
                teaser_dur = max(0.5, intervals[0][1] - intervals[0][0])
                t_end_str = self.format_timestamp_ass(teaser_dur)
                total_end_str = self.format_timestamp_ass(max(0.5, total_duration))

                # During teaser (0.0 to teaser_dur): show eye-catching teaser cue
                dialogue_lines.append(
                    f"Dialogue: 1,{self.format_timestamp_ass(0.0)},{t_end_str},HookHeader,,0,0,0,,WAIT FOR IT..."
                )
                # During main story (teaser_dur to end): show authentic hook title from script
                formatted_hook = format_tiktok_hook_header(hook_header_text)
                dialogue_lines.append(
                    f"Dialogue: 1,{t_end_str},{total_end_str},HookHeader,,0,0,0,,{formatted_hook}"
                )
            else:
                formatted_hook = format_tiktok_hook_header(hook_header_text)
                start_str = self.format_timestamp_ass(0.0)
                end_str = self.format_timestamp_ass(max(0.5, total_duration))
                dialogue_lines.append(
                    f"Dialogue: 1,{start_str},{end_str},HookHeader,,0,0,0,,{formatted_hook}"
                )

        # 2. Add animated spoken karaoke subtitles on Layer 0 across all intervals
        cumulative_time = 0.0
        for iv_start, iv_end in intervals:
            iv_dur = max(0.0, iv_end - iv_start)
            for seg in segments:
                seg_start = seg.get("start", 0.0)
                seg_end = seg.get("end", 0.0)
                words = seg.get("words", [])

                if seg_end <= iv_start or seg_start >= iv_end:
                    continue

                rel_start = cumulative_time + max(0.0, seg_start - iv_start)
                rel_end = cumulative_time + max(0.1, min(iv_dur, seg_end - iv_start))

                if words and len(words) > 0:
                    chunk_size = 4
                    for c in range(0, len(words), chunk_size):
                        chunk = words[c : c + chunk_size]
                        first_w_start = chunk[0].get("start", seg_start)
                        last_w_end = chunk[-1].get("end", seg_end)
                        if last_w_end <= iv_start or first_w_start >= iv_end:
                            continue

                        c_start = cumulative_time + max(0.0, first_w_start - iv_start)
                        c_end = cumulative_time + max(0.1, min(iv_dur, last_w_end - iv_start))

                        karaoke_parts = []
                        for w in chunk:
                            w_raw_start = w.get("start", seg_start)
                            w_raw_end = w.get("end", seg_end)
                            w_start = cumulative_time + max(0.0, w_raw_start - iv_start)
                            w_end = cumulative_time + max(0.05, min(iv_dur, w_raw_end - iv_start))
                            duration_cs = max(10, int((w_end - w_start) * 100))
                            word_str = strip_emojis(w.get("word", "")).strip()
                            if uppercase:
                                word_str = word_str.upper()
                            if not word_str:
                                continue

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
                    text = strip_emojis(seg.get("text", "")).strip()
                    if uppercase:
                        text = text.upper()
                    if text:
                        start_str = self.format_timestamp_ass(rel_start)
                        end_str = self.format_timestamp_ass(rel_end)
                        dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

            cumulative_time += iv_dur

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(dialogue_lines) + "\n")

        return out_file

    def generate_srt(
        self,
        segments: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        output_path: Path | str,
        keep_intervals: Optional[List[List[float]]] = None,
        part_index: Optional[int] = None,
        total_parts: Optional[int] = None,
        hook_header_text: Optional[str] = None,
    ) -> Path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        intervals = keep_intervals or [[clip_start, clip_end]]
        cumulative_time = 0.0
        srt_entries: List[str] = []
        counter = 1

        for iv_start, iv_end in intervals:
            iv_dur = max(0.0, iv_end - iv_start)
            for seg in segments:
                seg_start = seg.get("start", 0.0)
                seg_end = seg.get("end", 0.0)
                if seg_end <= iv_start or seg_start >= iv_end:
                    continue

                rel_start = cumulative_time + max(0.0, seg_start - iv_start)
                rel_end = cumulative_time + max(0.1, min(iv_dur, seg_end - iv_start))
                text = strip_emojis(seg.get("text", "")).strip()

                if text:
                    srt_entries.append(
                        f"{counter}\n{self.format_timestamp_srt(rel_start)} --> {self.format_timestamp_srt(rel_end)}\n{text}\n"
                    )
                    counter += 1
            cumulative_time += iv_dur

        with open(out_file, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_entries))

        return out_file


captioner = CaptionGenerator()
CaptionService = CaptionGenerator

