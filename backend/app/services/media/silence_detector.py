"""Silence and Dead-Air Detector using FFmpeg analysis."""

import asyncio
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SilenceInterval(BaseModel):
    start: float
    end: float
    duration: float


class TimelineEdit(BaseModel):
    source_start: float
    source_end: float
    keep: List[List[float]]
    dead_air_removed_seconds: float


class SilenceDetector:
    """Detects silence and dead-air intervals in audio/video media."""

    def __init__(self, noise_db: float = -35.0, min_silence_sec: float = 0.45):
        self.noise_db = noise_db
        self.min_silence_sec = min_silence_sec

    async def detect_silence(
        self,
        media_path: Path,
        noise_db: float = -35.0,
        min_silence_sec: float = 0.45,
    ) -> List[SilenceInterval]:
        """
        Run FFmpeg silencedetect filter to extract quiet audio regions.
        """
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i", str(media_path),
            "-af", f"silencedetect=noise={noise_db}dB:d={min_silence_sec}",
            "-f", "null",
            "-",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        output = stderr.decode("utf-8", errors="replace")

        silence_intervals: List[SilenceInterval] = []
        current_start: float | None = None

        for line in output.splitlines():
            # silence_start: 12.45
            match_start = re.search(r"silence_start:\s*([0-9.]+)", line)
            if match_start:
                current_start = float(match_start.group(1))

            # silence_end: 15.20 | silence_duration: 2.75
            match_end = re.search(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", line)
            if match_end and current_start is not None:
                end_time = float(match_end.group(1))
                duration = float(match_end.group(2))
                silence_intervals.append(SilenceInterval(
                    start=current_start,
                    end=end_time,
                    duration=duration,
                ))
                current_start = None

        return silence_intervals

    def build_edited_timeline(
        self,
        start_time: float,
        end_time: float,
        silence_intervals: List[SilenceInterval],
        dead_air_threshold_sec: float = 1.2,
        preserve_buffer_sec: float = 0.15,
    ) -> TimelineEdit:
        """
        Build kept timeline slices [ [t1, t2], [t3, t4] ] for a candidate window [start_time, end_time].
        Removes dead-air gaps exceeding dead_air_threshold_sec while maintaining natural speech buffers.
        """
        if end_time <= start_time:
            return TimelineEdit(
                source_start=start_time,
                source_end=end_time,
                keep=[[start_time, end_time]],
                dead_air_removed_seconds=0.0,
            )

        # Filter silences that intersect the candidate window and exceed dead-air threshold
        dead_air_cuts: List[Tuple[float, float]] = []
        for s in silence_intervals:
            if s.duration >= dead_air_threshold_sec:
                # Find overlap with candidate window
                c_start = max(start_time, s.start + preserve_buffer_sec)
                c_end = min(end_time, s.end - preserve_buffer_sec)
                if c_end > c_start + 0.3:  # Only cut if remaining dead air is meaningful (>0.3s)
                    dead_air_cuts.append((c_start, c_end))

        if not dead_air_cuts:
            return TimelineEdit(
                source_start=start_time,
                source_end=end_time,
                keep=[[start_time, end_time]],
                dead_air_removed_seconds=0.0,
            )

        # Sort and merge cuts
        dead_air_cuts.sort(key=lambda x: x[0])
        merged_cuts: List[Tuple[float, float]] = []
        for c in dead_air_cuts:
            if not merged_cuts:
                merged_cuts.append(c)
            else:
                last_start, last_end = merged_cuts[-1]
                if c[0] <= last_end:
                    merged_cuts[-1] = (last_start, max(last_end, c[1]))
                else:
                    merged_cuts.append(c)

        # Build kept intervals
        keep_intervals: List[List[float]] = []
        cursor = start_time
        total_removed = 0.0

        for cut_start, cut_end in merged_cuts:
            if cut_start > cursor + 0.1:
                keep_intervals.append([round(cursor, 3), round(cut_start, 3)])
            total_removed += (cut_end - cut_start)
            cursor = cut_end

        if cursor < end_time - 0.1:
            keep_intervals.append([round(cursor, 3), round(end_time, 3)])

        if not keep_intervals:
            keep_intervals = [[start_time, end_time]]
            total_removed = 0.0

        return TimelineEdit(
            source_start=start_time,
            source_end=end_time,
            keep=keep_intervals,
            dead_air_removed_seconds=round(total_removed, 3),
        )


silence_detector = SilenceDetector()
