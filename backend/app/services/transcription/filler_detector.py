"""Filler word and false-start detection service."""

import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

COMMON_FILLERS = {
    "um", "uh", "uhm", "erm", "ah", "like", "you know", "i mean", "so basically",
    "kind of", "sort of", "literally", "actually", "right?", "you see"
}


class FillerOccurrence(BaseModel):
    token: str
    start: float
    end: float
    is_filler: bool
    context: str


class FillerDetector:
    """Detects filler words, stutter repetitions, and false starts in speech segments."""

    def analyze_segments(
        self,
        segments: List[Dict[str, Any]],
    ) -> List[FillerOccurrence]:
        """
        Analyze transcript segments and word-level timestamps to locate filler expressions.
        """
        findings: List[FillerOccurrence] = []

        for seg in segments:
            text = seg.get("text", "").strip()
            words = seg.get("words", [])

            # Word-level checking if available
            if words:
                for idx, w in enumerate(words):
                    word_clean = re.sub(r"[^\w]", "", w.get("word", "")).lower()
                    if word_clean in {"um", "uh", "uhm", "erm", "ah"}:
                        findings.append(FillerOccurrence(
                            token=word_clean,
                            start=w.get("start", seg.get("start", 0.0)),
                            end=w.get("end", seg.get("end", 0.0)),
                            is_filler=True,
                            context=text,
                        ))
                    elif idx > 0 and word_clean == re.sub(r"[^\w]", "", words[idx - 1].get("word", "")).lower():
                        # Repeated word stutter: "I I think"
                        findings.append(FillerOccurrence(
                            token=f"repeat:{word_clean}",
                            start=w.get("start", seg.get("start", 0.0)),
                            end=w.get("end", seg.get("end", 0.0)),
                            is_filler=True,
                            context=f"Stutter repeat: {word_clean}",
                        ))
            else:
                # Segment-level regex detection
                for filler in ["\\bum\\b", "\\buh\\b", "\\buhm\\b", "\\bah\\b"]:
                    if re.search(filler, text, re.IGNORECASE):
                        findings.append(FillerOccurrence(
                            token=filler.replace("\\b", ""),
                            start=seg.get("start", 0.0),
                            end=seg.get("end", 0.0),
                            is_filler=True,
                            context=text,
                        ))

        return findings


filler_detector = FillerDetector()
