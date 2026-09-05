"""
Audio Hook & Linguistic Momentum Analyzer.
Extracts high-retention opening hooks, narrative arcs, and contextual platform metadata
directly from spoken audio dialogue transcripts with multi-genre and 10s intense hook evaluation.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
from app.services.ai.base import PlatformClipMetadata, RawCandidateMoment

# Emoji and Non-Standard Symbol Stripper for Subtitles & ASS Burn-in
EMOJI_PATTERN = re.compile(
    "["
    "\U00010000-\U0010ffff"  # Supplemental Multilingual Plane (all emojis, symbols)
    "\u2600-\u27bf"          # Miscellaneous Symbols and Dingbats
    "\u2300-\u23ff"          # Miscellaneous Technical
    "\u2b50-\u2b55"          # Star symbols, etc.
    "\u200d"                 # Zero-width joiner
    "\ufe0f"                 # Variation selector 16 (emoji style)
    "\ufe0e"                 # Variation selector 15 (text style)
    "]+",
    flags=re.UNICODE,
)

HOOK_QUESTION_STARTERS = (
    "why", "how", "what", "where", "who", "when", "can", "could",
    "would", "should", "did", "do", "does", "have", "has", "is", "are"
)

CONTRARIAN_KEYWORDS = [
    "never", "stop", "mistake", "wrong", "lie", "secret", "truth",
    "nobody", "scam", "ruined", "warning", "fake", "actually", "hidden",
    "myth", "worse", "worst", "banned", "illegal", "expose", "exposed"
]

HIGH_RETENTION_KEYWORDS = [
    "insane", "crazy", "unbelievable", "shocking", "screaming", "crying",
    "destroyed", "caught", "panic", "disaster", "plot twist", "happened",
    "realized", "discovered", "unexpected", "mind-blowing", "listen"
]

# Action, POV Pursuits, Bodycam & Chaos Hooks
CHAOS_ACTION_KEYWORDS = [
    "stop", "get down", "hands up", "run", "chase", "officer", "suspect",
    "watch out", "look out", "drop it", "faster", "bike", "crash", "danger",
    "caught", "busted", "behind you", "move move", "freeze", "don't move",
    "gun", "weapon", "call 911", "emergency", "backup", "he's running",
    "got him", "pulled over", "pursuit", "speeding", "takedown"
]

# Arguments, Heated Clashes & Screaming
ARGUMENT_CLASH_KEYWORDS = [
    "shut up", "don't touch", "get out", "you're lying", "screaming",
    "freaking out", "fight", "brawl", "call the cops", "what are you doing",
    "holy shit", "oh my god", "no way", "you idiot", "back off", "get lost",
    "are you kidding", "don't talk to me", "excuse me", "out of control"
]

# Military, History & Tactical Secrets
MILITARY_HISTORY_KEYWORDS = [
    "war", "attack", "invasion", "secret mission", "bomber", "strike",
    "classified", "declassified", "weapon", "ambush", "surrender", "casualty",
    "conspiracy", "unknown fact", "battle", "artillery", "soldier", "troops",
    "navy", "air force", "army", "operation", "historical", "wwii", "vietnam"
]

# Nostalgia & Retro Memories
NOSTALGIA_KEYWORDS = [
    "remember when", "back in the day", "discontinued", "forgotten",
    "grew up with", "childhood", "90s", "2000s", "retro", "nobody uses this",
    "nostalgic", "throwback", "old school", "used to have", "can't believe we"
]

# Penalties for slow, boring, calm introductions in the first 10 seconds
CALM_INTRO_PENALTIES = [
    "welcome back", "hey guys", "hey everyone", "in this video", "today we are",
    "today i am", "so basically", "thanks for watching", "make sure to subscribe",
    "in today's episode", "as we all know", "hello everyone", "good morning"
]

PAYOFF_MARKERS = [
    "that is why", "that's why", "so that's", "the reason is", "which means",
    "in conclusion", "the result", "the takeaway", "the lesson", "remember",
    "at the end of the day", "bottom line", "and that changed", "now you know",
    "that's how", "that is how"
]

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "this", "that", "these", "those", "is", "am", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "it", "its", "you", "your", "he", "him", "his", "she", "her", "they",
    "them", "their", "we", "us", "our", "i", "me", "my", "so", "if",
    "just", "like", "know", "then", "there", "here", "what", "who", "which"
}


def strip_emojis(text: str) -> str:
    """
    Remove Unicode emojis and decorative pictographs from text.
    Guarantees clean rendering without missing character boxes (□) in FFmpeg libass subtitles.
    """
    if not text:
        return ""
    no_emoji = EMOJI_PATTERN.sub("", text)
    clean = re.sub(r"\s+", " ", no_emoji).strip()
    return clean


def extract_topic_keywords(transcript: str, top_n: int = 5) -> List[str]:
    """Extract salient, meaningful topic keywords from the spoken dialogue."""
    clean = re.sub(r"[^\w\s]", " ", transcript.lower())
    words = clean.split()
    counts: Dict[str, int] = {}
    for w in words:
        if len(w) >= 4 and w not in STOP_WORDS and not w.isdigit():
            counts[w] = counts.get(w, 0) + 1

    sorted_words = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]


def clean_hook_title(text: str, max_words: int = 9) -> str:
    """Format a spoken sentence into a punchy, clean title without punctuation noise or emojis."""
    clean = strip_emojis(text).strip()
    clean = re.sub(r"^[\"']|[\"']$", "", clean).strip()
    clean = clean.rstrip(".,;:- ")
    words = clean.split()
    if len(words) > max_words:
        clean = " ".join(words[:max_words])
    return clean


def build_single_para_post(
    title: str,
    caption: str,
    hashtags: List[str],
    part_index: Optional[int] = None,
    total_parts: Optional[int] = None,
) -> str:
    """Format a ready-to-paste single paragraph combining title, description, and hashtags."""
    t = title.strip()
    c = caption.strip().replace("\n", " ")
    c = re.sub(r"\s+", " ", c)
    tags_str = " ".join(hashtags)
    part_prefix = f"Part {part_index}/{total_parts}: " if (part_index and total_parts and total_parts > 1) else ""
    if t in c:
        return f"{part_prefix}{c} {tags_str}".strip()
    return f"{part_prefix}{t} — {c} {tags_str}".strip()


class AudioHookAnalyzer:
    """
    Analyzes spoken audio transcript timestamps and linguistic patterns
    to discover high-velocity hooks (chaos, fights, arguments, police POV, history, nostalgia),
    optimal narrative boundaries, and contextual metadata.
    """

    def score_opening_hook(self, text: str, word_count: int, genre: Optional[str] = None) -> Tuple[float, str]:
        """
        Evaluate the hook strength of the opening 10-15 seconds.
        Prefers chaos, fights, arguments, high-stakes pursuits, direct questions, and contrarian claims.
        Penalizes calm, slow setups or pleasantries.
        """
        lower = text.lower().strip()
        score = 72.0
        reasons = []

        # 1. Action, POV Pursuits, Police Cam & Chaos (Highest Adrenaline Boost)
        action_hits = [w for w in CHAOS_ACTION_KEYWORDS if w in lower]
        if action_hits:
            score += min(24.0, 14.0 + len(action_hits) * 3.5)
            reasons.append(f"High-adrenaline action/pursuit ('{action_hits[0]}')")

        # 2. Arguments, Heated Clashes & Screaming
        argument_hits = [w for w in ARGUMENT_CLASH_KEYWORDS if w in lower]
        if argument_hits:
            score += min(22.0, 14.0 + len(argument_hits) * 3.0)
            reasons.append(f"Intense argument/clash ('{argument_hits[0]}')")

        # 3. Direct Question Hooks (High curiosity & immediate engagement)
        if "?" in text or any(lower.startswith(q + " ") for q in HOOK_QUESTION_STARTERS):
            score += 16.0
            reasons.append("Direct question creates curiosity")

        # 4. Contrarian / Myth-Busting Hooks (Pattern Interrupt)
        contrarian_hits = [w for w in CONTRARIAN_KEYWORDS if w in lower]
        if contrarian_hits:
            score += min(18.0, 10.0 + len(contrarian_hits) * 3.0)
            reasons.append(f"Contrarian trigger ('{contrarian_hits[0]}')")

        # 5. Military / History Secrets & Nostalgia Triggers
        history_hits = [w for w in MILITARY_HISTORY_KEYWORDS if w in lower]
        if history_hits:
            score += min(16.0, 8.0 + len(history_hits) * 2.5)
            reasons.append(f"Historical stakes ('{history_hits[0]}')")

        nostalgia_hits = [w for w in NOSTALGIA_KEYWORDS if w in lower]
        if nostalgia_hits:
            score += min(16.0, 10.0 + len(nostalgia_hits) * 3.0)
            reasons.append("Nostalgia recognition hook")

        # 6. High-Intensity Emotional Triggers
        retention_hits = [w for w in HIGH_RETENTION_KEYWORDS if w in lower]
        if retention_hits:
            score += min(14.0, 8.0 + len(retention_hits) * 2.5)
            reasons.append(f"High-impact emphasis ('{retention_hits[0]}')")

        # 7. Strict penalty for calm introductory fluff in first 10s
        for calm_phrase in CALM_INTRO_PENALTIES:
            if calm_phrase in lower:
                score -= 22.0
                reasons.append(f"Slow/calm intro penalty ('{calm_phrase}')")
                break

        # 8. Phrasing velocity
        first_clause = re.split(r"[.?!,]", text)[0].strip()
        first_words = first_clause.split()
        if len(first_words) > 18:
            score -= 6.0
            reasons.append("Meandering setup")
        elif 3 <= len(first_words) <= 10:
            score += 5.0
            reasons.append("Punchy opening")

        final_score = max(40.0, min(99.0, score))
        summary = "; ".join(reasons) if reasons else "Conversational opening"
        return round(final_score, 1), summary

    def score_payoff_resolution(self, text: str) -> Tuple[float, str]:
        """Evaluate how cleanly the clip concludes with a payoff or clear takeaway."""
        lower = text.lower().strip()
        score = 72.0
        reasons = []

        if any(pm in lower for pm in PAYOFF_MARKERS):
            score += 20.0
            reasons.append("Explicit takeaway statement")

        if text.endswith((".", "!", "?")):
            score += 5.0
            reasons.append("Natural completion boundary")

        final_score = max(55.0, min(96.0, score))
        summary = "; ".join(reasons) if reasons else "Natural conclusion"
        return round(final_score, 1), summary

    def find_peak_climax_moment(
        self,
        transcript_segments: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        genre: Optional[str] = None,
        target_climax_duration: float = 6.0,
    ) -> Tuple[float, float, str]:
        """
        Locate the single most explosive 5-8 second climax/fight/chaos/argument window
        inside the clip (preferring moments in the middle-to-end of the clip, from clip_start + 4.0 onwards).
        Returns (climax_start, climax_end, climax_summary).
        """
        dur = clip_end - clip_start
        if dur < 10.0:
            mid = round(clip_start + dur * 0.5, 2)
            return mid, clip_end, "Peak moment"

        clip_segs = [
            s for s in transcript_segments
            if float(s.get("end", 0.0)) > clip_start + 3.0 and float(s.get("start", 0.0)) < clip_end
        ]

        if not clip_segs:
            c_s = round(clip_start + dur * 0.6, 2)
            c_e = round(min(clip_end, c_s + target_climax_duration), 2)
            return c_s, c_e, "Climactic resolution"

        best_score = -1.0
        best_window = None
        best_summary = "Climactic turning point"

        for seg in clip_segs:
            w_start = float(seg.get("start", clip_start))
            if w_start < clip_start + 4.0:
                continue
            w_end = min(clip_end, w_start + target_climax_duration)
            if w_end - w_start < 3.0:
                continue

            w_texts = []
            for s in clip_segs:
                s_s = float(s.get("start", 0.0))
                s_e = float(s.get("end", 0.0))
                if s_e > w_start and s_s < w_end:
                    w_texts.append(s.get("text", ""))

            combined = " ".join(w_texts).lower()
            intensity = 50.0

            chaos_hits = [k for k in CHAOS_ACTION_KEYWORDS if k in combined]
            intensity += len(chaos_hits) * 14.0

            arg_hits = [k for k in ARGUMENT_CLASH_KEYWORDS if k in combined]
            intensity += len(arg_hits) * 12.0

            exclamations = combined.count("!")
            intensity += min(15.0, exclamations * 5.0)

            ret_hits = [k for k in HIGH_RETENTION_KEYWORDS if k in combined]
            intensity += len(ret_hits) * 8.0

            w_count = len(combined.split())
            velocity = w_count / max(1.0, w_end - w_start)
            if velocity > 2.8:
                intensity += 8.0

            if intensity > best_score:
                best_score = intensity
                best_window = (round(w_start, 2), round(w_end, 2))
                key_phrase = chaos_hits[0] if chaos_hits else (arg_hits[0] if arg_hits else "Peak climax")
                best_summary = f"Peak intense moment ('{key_phrase}')"

        if best_window and best_window[1] > best_window[0] + 2.0:
            return best_window[0], best_window[1], best_summary

        c_s = round(clip_start + dur * 0.60, 2)
        c_e = round(min(clip_end, c_s + target_climax_duration), 2)
        return c_s, c_e, "Climactic resolution"

    def trim_calm_intro_to_hook(
        self,
        transcript_segments: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        genre: Optional[str] = None,
    ) -> float:
        """
        In direct chronological cut mode, ensures the clip does NOT start with calm greetings,
        dead air, or filler pleasantries ('welcome back', 'hey guys', silence).
        Scans opening segments and advances clip_start to the first segment that has genuine hook substance.
        """
        clip_segs = [
            s for s in transcript_segments
            if float(s.get("end", 0.0)) > clip_start and float(s.get("start", 0.0)) < min(clip_start + 14.0, clip_end)
        ]

        if not clip_segs:
            return clip_start

        for seg in clip_segs:
            text = seg.get("text", "").strip().lower()
            is_calm = any(calm in text for calm in CALM_INTRO_PENALTIES)
            if is_calm:
                continue

            has_action = any(k in text for k in CHAOS_ACTION_KEYWORDS)
            has_arg = any(k in text for k in ARGUMENT_CLASH_KEYWORDS)
            has_q = "?" in text or any(text.startswith(q + " ") for q in HOOK_QUESTION_STARTERS)
            has_excl = "!" in text
            words = text.split()

            if has_action or has_arg or has_q or has_excl or len(words) >= 4:
                seg_s = float(seg.get("start", clip_start))
                if clip_end - seg_s >= 15.0:
                    return round(seg_s, 2)

        return clip_start

    def extract_hook_headline_from_script(
        self,
        transcript_segments: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        genre: Optional[str] = None,
        max_words: int = 7,
    ) -> str:
        """
        Extracts an eye-catching, hooked headline directly analyzing the spoken dialogue of the clip.
        Prefers urgent commands, questions, shocking statements, or high-intensity phrases.
        """
        clip_segs = [
            s for s in transcript_segments
            if float(s.get("end", 0.0)) > clip_start and float(s.get("start", 0.0)) < clip_end
        ]

        if not clip_segs:
            return "WATCH TILL THE END"

        best_cand = ""
        best_score = -1.0

        for seg in clip_segs:
            raw = strip_emojis(seg.get("text", "")).strip()
            if not raw or len(raw.split()) < 2:
                continue
            lower = raw.lower()

            if any(c in lower for c in CALM_INTRO_PENALTIES):
                continue

            score = 10.0
            if any(k in lower for k in CHAOS_ACTION_KEYWORDS):
                score += 30.0
            if any(k in lower for k in ARGUMENT_CLASH_KEYWORDS):
                score += 28.0
            if "?" in raw:
                score += 20.0
            if "!" in raw:
                score += 15.0
            if any(k in lower for k in HIGH_RETENTION_KEYWORDS):
                score += 15.0

            w_len = len(raw.split())
            if 3 <= w_len <= 8:
                score += 10.0

            if score > best_score:
                best_score = score
                best_cand = clean_hook_title(raw, max_words=max_words).upper()

        if best_cand:
            return best_cand

        first_text = strip_emojis(clip_segs[0].get("text", "")).strip()
        cleaned = clean_hook_title(first_text, max_words=max_words).upper()
        return cleaned if cleaned else "WATCH TILL THE END"

    def discover_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        requested_count: int,
        duration_target: str = "30-45s",
        mode: str = "viral_moments",
        genre: Optional[str] = None,
    ) -> List[RawCandidateMoment]:
        """
        Discovers candidate moments anchored to high-retention spoken dialogue hooks.
        Ensures the first 10 seconds captivate the viewer and starts right on the hook.
        """
        if not transcript_segments:
            return []

        target_min = 25.0
        target_max = 50.0
        if "15-30" in duration_target:
            target_min, target_max = 15.0, 32.0
        elif "30-45" in duration_target:
            target_min, target_max = 28.0, 48.0
        elif "45-60" in duration_target:
            target_min, target_max = 42.0, 62.0
        elif "60-90" in duration_target:
            target_min, target_max = 58.0, 95.0

        total_dur = float(media_info.get("duration_seconds") or 60.0)
        target_min = min(target_min, max(3.0, total_dur * 0.4))
        target_max = min(target_max, total_dur)

        num_segs = len(transcript_segments)
        candidates: List[RawCandidateMoment] = []

        active_genre = genre or media_info.get("genre") or mode

        for i in range(num_segs):
            start_seg = transcript_segments[i]
            start_time = float(start_seg.get("start", 0.0))
            if start_time >= total_dur - 4.0:
                continue

            start_text = start_seg.get("text", "").strip()
            if not start_text or len(start_text.split()) < 2:
                continue

            words = start_seg.get("words", [])
            if words and len(words) > 0:
                first_w_start = words[0].get("start")
                if first_w_start is not None:
                    start_time = float(first_w_start)

            hook_score, hook_reason = self.score_opening_hook(start_text, len(start_text.split()), genre=active_genre)

            accumulated_text = []
            best_end_seg = None
            best_end_time = start_time + target_min

            for j in range(i, num_segs):
                seg = transcript_segments[j]
                seg_end = float(seg.get("end", start_time + 30.0))
                seg_text = seg.get("text", "").strip()
                accumulated_text.append(seg_text)
                cur_dur = seg_end - start_time

                if cur_dur >= target_min and seg_end <= total_dur:
                    is_terminal = seg_text.endswith((".", "!", "?"))
                    payoff_score, payoff_reason = self.score_payoff_resolution(seg_text)

                    if is_terminal or cur_dur >= target_max or payoff_score > 80.0:
                        best_end_seg = seg
                        best_end_time = seg_end
                        break
                    elif best_end_seg is None:
                        best_end_seg = seg
                        best_end_time = seg_end

                if cur_dur > target_max:
                    break

            if best_end_seg is None or (best_end_time - start_time) < target_min * 0.85:
                continue

            end_text = best_end_seg.get("text", "").strip()
            payoff_score, payoff_reason = self.score_payoff_resolution(end_text)

            end_words = best_end_seg.get("words", [])
            if end_words and len(end_words) > 0:
                last_w_end = end_words[-1].get("end")
                if last_w_end is not None:
                    best_end_time = float(last_w_end)

            clip_dur = round(best_end_time - start_time, 2)
            if clip_dur < 4.0:
                continue

            combined_text = " ".join(accumulated_text)
            total_words = len(combined_text.split())
            word_velocity = total_words / max(1.0, clip_dur)

            retention_score = min(98.0, 70.0 + (hook_score - 70.0) * 0.4 + (payoff_score - 70.0) * 0.3 + min(15.0, word_velocity * 4.0))
            curiosity_score = min(98.0, hook_score * 0.95 + 4.0)
            story_score = min(96.0, 75.0 + min(15.0, (total_words / 15.0) * 2.5))
            emotion_score = min(95.0, 74.0 + (hook_score * 0.2))
            shareability_score = min(95.0, 72.0 + (payoff_score * 0.25))
            novelty_score = min(94.0, 72.0 + (i % 12))
            quotability_score = min(96.0, 75.0 + (payoff_score * 0.2))

            # Real climax detection: Find true peak 5-7s moment of highest intensity in the clip
            c_s, c_e, c_sum = self.find_peak_climax_moment(
                transcript_segments=transcript_segments,
                clip_start=start_time,
                clip_end=best_end_time,
                genre=active_genre,
                target_climax_duration=6.0,
            )

            # Analyze authentic spoken script to produce punchy headline
            hook_title = self.extract_hook_headline_from_script(
                transcript_segments=transcript_segments,
                clip_start=start_time,
                clip_end=best_end_time,
                genre=active_genre,
            )
            payoff_clean = clean_hook_title(end_text, max_words=8)

            candidates.append(
                RawCandidateMoment(
                    start=round(start_time, 2),
                    end=round(best_end_time, 2),
                    climax_start=c_s,
                    climax_end=c_e,
                    climax_summary=c_sum,
                    hook_score=round(hook_score, 1),
                    retention_score=round(retention_score, 1),
                    curiosity_score=round(curiosity_score, 1),
                    emotion_score=round(emotion_score, 1),
                    story_score=round(story_score, 1),
                    payoff_score=round(payoff_score, 1),
                    shareability_score=round(shareability_score, 1),
                    novelty_score=round(novelty_score, 1),
                    quotability_score=round(quotability_score, 1),
                    standalone_score=round(min(98.0, story_score * 0.95 + 4.0), 1),
                    rewatch_score=round(min(96.0, (hook_score + retention_score) / 2.0), 1),
                    visual_score=84.0,
                    audio_score=88.0,
                    platform_score=89.0,
                    reason=f"[{active_genre}] 10s Hook: \"{start_text[:50]}...\" ({hook_reason}). Payoff: \"{end_text[:40]}...\".",
                    hook_summary=hook_title,
                    payoff_summary=payoff_clean,
                )
            )

        candidates.sort(
            key=lambda c: c.hook_score * 0.45 + c.retention_score * 0.35 + c.payoff_score * 0.20,
            reverse=True,
        )

        needed_pool = max(requested_count * 5, 30)
        return candidates[:needed_pool]

    def generate_clip_metadata(
        self,
        clip_transcript: str,
        hook_summary: str,
        payoff_summary: str,
        part_index: Optional[int] = None,
        total_parts: Optional[int] = None,
        video_title: Optional[str] = None,
    ) -> PlatformClipMetadata:
        """
        Generates realistic, meaningful social metadata directly summarizing the spoken dialogue.
        Supports multi-part series tagging (e.g. 'PART 1/5') and single-paragraph copy export.
        """
        clean_text = strip_emojis(clip_transcript).strip()
        first_clause = re.split(r"[.?!]", clean_text)[0].strip() if clean_text else "High-Impact Short Clip"

        base_title = hook_summary.strip() or first_clause
        base_title = clean_hook_title(base_title, max_words=9)
        if len(base_title) < 8:
            base_title = clean_hook_title(video_title or "Unbelievable Moment", max_words=8)

        if part_index and total_parts:
            title = f"PART {part_index}/{total_parts}: {base_title}"
        else:
            title = base_title

        keywords = extract_topic_keywords(clean_text, top_n=4)
        hashtags = [f"#{kw}" for kw in keywords]
        base_tags = ["#fyp", "#viral", "#shorts", "#mustwatch", "#trending"]
        if part_index:
            base_tags.insert(0, f"#part{part_index}")
        combined_tags = (hashtags + [t for t in base_tags if t not in hashtags])[:5]

        # TikTok
        tt_title = title[:75]
        part_cta = f" Follow for Part {part_index + 1}! 🎬" if part_index and total_parts and part_index < total_parts else ""
        tt_caption = f"{title}. {first_clause[:100]}...{part_cta}\n\n{' '.join(combined_tags)}"

        # Reels
        reels_caption = (
            f"{title}\n\n"
            f"\"{clean_text[:140]}...\"\n\n"
            f"📌 Save this for later | 📲 Share with someone who needs this{part_cta}\n\n"
            f"{' '.join(combined_tags)}"
        )

        # Shorts
        shorts_title = f"{title[:45]} #shorts"
        shorts_desc = (
            f"{clean_text[:200]}...{part_cta}\n\n"
            f"Subscribe for more daily clips!\n\n"
            f"{' '.join(combined_tags)}"
        )

        single_para = build_single_para_post(title, tt_caption, combined_tags)

        return PlatformClipMetadata(
            tiktok_title=tt_title,
            tiktok_caption=tt_caption,
            tiktok_hashtags=combined_tags,
            reels_caption=reels_caption,
            reels_hashtags=combined_tags,
            shorts_title=shorts_title,
            shorts_description=shorts_desc,
            shorts_hashtags=combined_tags,
            single_para_copy=single_para,
            part_index=part_index,
            total_parts=total_parts,
        )


audio_hook_analyzer = AudioHookAnalyzer()
AudioScriptAnalyzer = AudioHookAnalyzer
audio_analyzer = audio_hook_analyzer

