"""
Audio Hook & Linguistic Momentum Analyzer.
Extracts high-retention opening hooks, narrative arcs, and contextual platform metadata
directly from spoken audio dialogue transcripts.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
from app.services.ai.base import PlatformClipMetadata, RawCandidateMoment

# Emoji and Non-Standard Symbol Stripper for Subtitles & ASS Burn-in
# Standard fonts (Arial Black, Impact, Georgia, etc.) in FFmpeg/libass lack emoji glyphs
# and render missing character tofu boxes (□). This regex removes all such symbols.
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
    # Strip emojis matching the SMP range and symbols
    no_emoji = EMOJI_PATTERN.sub("", text)
    # Strip extra whitespace created by removing emojis
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
    # Remove surrounding quotes
    clean = re.sub(r"^[\"']|[\"']$", "", clean).strip()
    # Remove trailing periods, commas, or semicolons
    clean = clean.rstrip(".,;:- ")
    words = clean.split()
    if len(words) > max_words:
        clean = " ".join(words[:max_words])
    return clean


class AudioHookAnalyzer:
    """
    Analyzes spoken audio transcript timestamps and linguistic patterns
    to discover high-velocity hooks, optimal narrative boundaries, and contextual metadata.
    """

    def score_opening_hook(self, text: str, word_count: int) -> Tuple[float, str]:
        """
        Evaluate the hook strength of the opening 10-15 seconds.
        Prefers direct questions, contrarian claims, surprising revelations, and high linguistic velocity.
        """
        lower = text.lower().strip()
        score = 70.0
        reasons = []

        # 1. Direct Question Hooks (Highest curiosity & immediate engagement)
        if "?" in text or any(lower.startswith(q + " ") for q in HOOK_QUESTION_STARTERS):
            score += 20.0
            reasons.append("Direct question creates immediate curiosity")

        # 2. Contrarian / Myth-Busting Hooks (Stops scrolling immediately)
        contrarian_hits = [w for w in CONTRARIAN_KEYWORDS if w in lower]
        if contrarian_hits:
            score += min(22.0, 12.0 + len(contrarian_hits) * 4.0)
            reasons.append(f"Contrarian trigger ('{contrarian_hits[0]}')")

        # 3. High-Intensity Emotional Triggers
        retention_hits = [w for w in HIGH_RETENTION_KEYWORDS if w in lower]
        if retention_hits:
            score += min(18.0, 10.0 + len(retention_hits) * 3.5)
            reasons.append(f"High-impact emphasis ('{retention_hits[0]}')")

        # 4. Numbers and Quantitative Proof
        if re.search(r"\b\d+[%kKmMbB]?\b", lower) or "$" in text:
            score += 8.0
            reasons.append("Concrete quantitative detail")

        # 5. Length penalty: Weak, slow setup (> 20 words before first punctuation)
        first_clause = re.split(r"[.?!,]", text)[0].strip()
        first_words = first_clause.split()
        if len(first_words) > 18:
            score -= 8.0
            reasons.append("Opening sentence is too long/meandering")
        elif 4 <= len(first_words) <= 12:
            score += 6.0
            reasons.append("Punchy, concise opening phrasing")

        final_score = max(55.0, min(98.0, score))
        summary = "; ".join(reasons) if reasons else "Engaging conversational opening"
        return round(final_score, 1), summary

    def score_payoff_resolution(self, text: str) -> Tuple[float, str]:
        """Evaluate how cleanly the clip concludes with a payoff or clear takeaway."""
        lower = text.lower().strip()
        score = 72.0
        reasons = []

        if any(pm in lower for pm in PAYOFF_MARKERS):
            score += 20.0
            reasons.append("Explicit takeaway or conclusion statement")

        if text.endswith((".", "!", "?")):
            score += 5.0
            reasons.append("Natural sentence completion boundary")

        final_score = max(60.0, min(96.0, score))
        summary = "; ".join(reasons) if reasons else "Natural conclusion"
        return round(final_score, 1), summary

    def discover_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        requested_count: int,
        duration_target: str = "30-45s",
        mode: str = "podcast",
    ) -> List[RawCandidateMoment]:
        """
        Discovers candidate moments anchored to high-retention spoken dialogue hooks.
        Ensures the first 10-15 seconds captivate the viewer and starts right on the hook.
        """
        if not transcript_segments:
            return []

        # Parse target duration
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

        # Step through every transcript segment as a potential hook opening
        for i in range(num_segs):
            start_seg = transcript_segments[i]
            start_time = float(start_seg.get("start", 0.0))
            if start_time >= total_dur - 4.0:
                continue

            start_text = start_seg.get("text", "").strip()
            if not start_text or len(start_text.split()) < 2:
                continue

            # Snap start_time cleanly to the first spoken word if word timestamps exist
            words = start_seg.get("words", [])
            if words and len(words) > 0:
                first_w_start = words[0].get("start")
                if first_w_start is not None:
                    start_time = float(first_w_start)

            hook_score, hook_reason = self.score_opening_hook(start_text, len(start_text.split()))

            # Slide forward to accumulate narrative context up to target duration
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
                    # Check if this segment represents a good boundary (sentence terminal)
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

            # Snap end_time cleanly to the last spoken word
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
            word_velocity = total_words / max(1.0, clip_dur)  # words per second

            # Linguistic retention score
            retention_score = min(98.0, 70.0 + (hook_score - 70.0) * 0.4 + (payoff_score - 70.0) * 0.3 + min(15.0, word_velocity * 4.0))
            curiosity_score = min(98.0, hook_score * 0.95 + 4.0)
            story_score = min(96.0, 75.0 + min(15.0, (total_words / 15.0) * 2.5))
            emotion_score = min(95.0, 74.0 + (hook_score * 0.2))
            shareability_score = min(95.0, 72.0 + (payoff_score * 0.25))
            novelty_score = min(94.0, 72.0 + (i % 12))
            quotability_score = min(96.0, 75.0 + (payoff_score * 0.2))

            # Climax anchor (peak narrative moment inside clip)
            c_s = round(start_time + clip_dur * 0.55, 2)
            c_e = round(min(best_end_time, c_s + 4.0), 2)

            hook_title = clean_hook_title(start_text, max_words=9)
            payoff_clean = clean_hook_title(end_text, max_words=8)

            candidates.append(
                RawCandidateMoment(
                    start=round(start_time, 2),
                    end=round(best_end_time, 2),
                    climax_start=c_s,
                    climax_end=c_e,
                    climax_summary=f"Climactic moment: {payoff_clean}",
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
                    reason=f"[{mode}] Opening hook: \"{start_text[:50]}...\" ({hook_reason}). Clean payoff: \"{end_text[:40]}...\".",
                    hook_summary=hook_title,
                    payoff_summary=payoff_clean,
                )
            )

        # Sort candidates by retention momentum
        candidates.sort(
            key=lambda c: c.hook_score * 0.40 + c.retention_score * 0.35 + c.payoff_score * 0.25,
            reverse=True,
        )

        # Limit to top requested candidates
        needed_pool = max(requested_count * 4, 25)
        return candidates[:needed_pool]

    def generate_clip_metadata(
        self,
        clip_transcript: str,
        hook_summary: str,
        payoff_summary: str,
    ) -> PlatformClipMetadata:
        """
        Generates realistic, meaningful social metadata directly summarizing the spoken dialogue.
        Derives accurate titles, captions, and platform hashtags from the spoken words.
        """
        clean_text = strip_emojis(clip_transcript).strip()
        first_clause = re.split(r"[.?!]", clean_text)[0].strip() if clean_text else "Insightful Clip"
        
        # Determine title from the genuine hook summary or first sentence
        title = hook_summary.strip() or first_clause
        title = clean_hook_title(title, max_words=9)
        if len(title) < 8:
            title = "Key Takeaway from This Discussion"

        # Topic keywords for hashtags
        keywords = extract_topic_keywords(clean_text, top_n=4)
        hashtags = [f"#{kw}" for kw in keywords]
        base_tags = ["#fyp", "#viral", "#shorts", "#mustwatch", "#trending"]
        combined_tags = (hashtags + [t for t in base_tags if t not in hashtags])[:5]

        # TikTok: Hook title, brief summary of dialogue, engaging open question
        tt_title = title[:75]
        tt_caption = (
            f"{title}. {first_clause[:100]}...\n\n"
            f"What's your take on this? Let me know below! 👇\n\n"
            f"{' '.join(combined_tags)}"
        )

        # Reels: Aesthetic, clean takeaway, save CTA
        reels_caption = (
            f"{title}\n\n"
            f"\"{clean_text[:140]}...\"\n\n"
            f"📌 Save this for later | 📲 Share with someone who needs this\n\n"
            f"{' '.join(combined_tags)}"
        )

        # Shorts: Punchy title with #shorts, detailed description
        shorts_title = f"{title[:45]} #shorts"
        shorts_desc = (
            f"{clean_text[:220]}...\n\n"
            f"Subscribe for more high-impact daily insights!\n\n"
            f"{' '.join(combined_tags)}"
        )

        return PlatformClipMetadata(
            tiktok_title=tt_title,
            tiktok_caption=tt_caption,
            tiktok_hashtags=combined_tags,
            reels_caption=reels_caption,
            reels_hashtags=combined_tags,
            shorts_title=shorts_title,
            shorts_description=shorts_desc,
            shorts_hashtags=combined_tags,
        )


audio_hook_analyzer = AudioHookAnalyzer()
