"""Video rendering service utilizing FFmpeg for 9:16 crop, timeline splicing, subtitle burn-in, and normalization."""

import asyncio
import logging
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.exceptions import MediaProcessingError

logger = logging.getLogger(__name__)


def retime_ass_subtitles(ass_content: str, keep_intervals: List[List[float]]) -> str:
    """
    Retime subtitle Dialogue events when dead-air intervals have been spliced out of the video.
    """
    if len(keep_intervals) <= 1:
        return ass_content

    # Helper to convert original timestamp to retimed timestamp
    def map_time(orig_sec: float) -> float:
        retimed_sec = 0.0
        for seg_start, seg_end in keep_intervals:
            if orig_sec < seg_start:
                break
            elif seg_start <= orig_sec <= seg_end:
                retimed_sec += (orig_sec - seg_start)
                break
            else:
                retimed_sec += (seg_end - seg_start)
        return retimed_sec

    def parse_ass_time(ts_str: str) -> float:
        parts = ts_str.strip().split(":")
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        return 0.0

    def format_ass_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h:d}:{m:02d}:{s:05.2f}"

    lines = ass_content.splitlines()
    new_lines = []
    for line in lines:
        if line.startswith("Dialogue:"):
            # Format: Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
            parts = line.split(",", 9)
            if len(parts) == 10:
                orig_start = parse_ass_time(parts[1])
                orig_end = parse_ass_time(parts[2])
                new_start = map_time(orig_start)
                new_end = map_time(orig_end)
                if new_end > new_start + 0.05:
                    parts[1] = format_ass_time(new_start)
                    parts[2] = format_ass_time(new_end)
                    new_lines.append(",".join(parts))
                    continue
        new_lines.append(line)

    return "\n".join(new_lines)


class VideoRenderer:
    """Renders sliced, vertically reframed, and captioned 9:16 video clips with FFmpeg."""

    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

    async def render_clip(
        self,
        source_video_path: Path | str,
        start_time: float,
        end_time: float,
        output_video_path: Path | str,
        reframing_config: Optional[Dict[str, Any]] = None,
        ass_subtitle_path: Optional[Path | str] = None,
        burn_captions: bool = True,
        keep_intervals: Optional[List[List[float]]] = None,
        framing_mode: str = "crop_9_16",
        blur_radius: int = 30,
    ) -> Path:
        """
        Renders a short-form video clip from source:
        - Accurately cuts between start_time and end_time (or slices multiple keep_intervals).
        - Applies selected framing mode:
            * crop_9_16: Full 9:16 vertical crop (TikTok / Reels / Shorts default)
            * blur_fit_9_16: 16:9 video centered within 9:16 vertical canvas with customized blurred background
            * original_16_9: Native 16:9 landscape widescreen
        - Burns in styled ASS subtitles if burn_captions is True.
        - Normalizes audio loudness (loudnorm).
        - Fully sanitizes all original video/container metadata.
        """
        src = Path(source_video_path).resolve()
        out = Path(output_video_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        intervals = keep_intervals or [[start_time, end_time]]
        # Filter valid intervals
        valid_intervals = [
            [float(s), float(e)] for s, e in intervals if float(e) > float(s) + 0.1
        ]
        if not valid_intervals:
            valid_intervals = [[start_time, end_time]]

        duration = sum(e - s for s, e in valid_intervals)
        crop_cfg = reframing_config or {}
        mode = framing_mode or "crop_9_16"
        r = max(5, min(100, blur_radius or 30))

        # Subtitle handling
        final_ass_path: Optional[Path] = None
        if burn_captions and ass_subtitle_path:
            p = Path(ass_subtitle_path).resolve()
            if p.exists():
                if len(valid_intervals) > 1:
                    # Retime subtitles to match spliced timeline
                    retimed_content = retime_ass_subtitles(p.read_text(encoding="utf-8"), valid_intervals)
                    retimed_path = p.with_name(f"{p.stem}_retimed.ass")
                    retimed_path.write_text(retimed_content, encoding="utf-8")
                    final_ass_path = retimed_path
                else:
                    final_ass_path = p

        # Check if single slice or multi-interval concat
        if len(valid_intervals) == 1:
            # Single slice: Fast seek with Lanczos sharp scaling
            s_time = valid_intervals[0][0]
            e_time = valid_intervals[0][1]
            seg_dur = max(0.5, e_time - s_time)

            if mode == "blur_fit_9_16":
                v_filter = (
                    f"split=2[bg_raw][fg_raw];"
                    f"[bg_raw]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT},boxblur={r}:5,drawbox=color=black@0.35:replace=1[bg];"
                    f"[fg_raw]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
                )
            elif mode == "original_16_9":
                v_filter = "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos"
            else:
                # Default: crop_9_16
                v_filter = f"scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}"

            if final_ass_path and final_ass_path.exists():
                escaped_ass = str(final_ass_path).replace("\\", "/").replace(":", "\\:")
                v_filter += f",subtitles='{escaped_ass}'"

            cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", f"{s_time:.3f}",
                "-i", str(src),
                "-t", f"{seg_dur:.3f}",
                "-vf", v_filter,
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level:v", "4.2",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "48000",
                "-map_metadata", "-1",
                "-map_metadata:s:v", "-1",
                "-map_metadata:s:a", "-1",
                "-map_chapters", "-1",
                "-fflags", "+bitexact",
                "-flags:v", "+bitexact",
                "-flags:a", "+bitexact",
                "-movflags", "+faststart",
                str(out)
            ]
        else:
            # Multi-segment splicing: Complex filtergraph with lanczos scaling
            filter_chunks = []
            concat_v_in = ""
            concat_a_in = ""
            for idx, (s, e) in enumerate(valid_intervals):
                filter_chunks.append(
                    f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{idx}]"
                )
                filter_chunks.append(
                    f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[a{idx}]"
                )
                concat_v_in += f"[v{idx}]"
                concat_a_in += f"[a{idx}]"

            num_segs = len(valid_intervals)
            filter_chunks.append(
                f"{concat_v_in}concat=n={num_segs}:v=1:a=0[vcat]"
            )
            filter_chunks.append(
                f"{concat_a_in}concat=n={num_segs}:v=0:a=1[acat]"
            )

            # Reframe & subtitle on spliced video with lanczos scaling
            if mode == "blur_fit_9_16":
                v_post = (
                    f"[vcat]split=2[bg_raw][fg_raw];"
                    f"[bg_raw]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT},boxblur={r}:5,drawbox=color=black@0.35:replace=1[bg];"
                    f"[fg_raw]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
                )
            elif mode == "original_16_9":
                v_post = "[vcat]scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos"
            else:
                v_post = f"[vcat]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}"

            if final_ass_path and final_ass_path.exists():
                escaped_ass = str(final_ass_path).replace("\\", "/").replace(":", "\\:")
                v_post += f",subtitles='{escaped_ass}'"
            v_post += "[vout]"
            filter_chunks.append(v_post)

            # Audio loudnorm on spliced audio
            filter_chunks.append("[acat]loudnorm=I=-14:TP=-1.0:LRA=11[aout]")

            full_filter = ";".join(filter_chunks)
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", str(src),
                "-filter_complex", full_filter,
                "-map", "[vout]",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level:v", "4.2",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "48000",
                "-map_metadata", "-1",
                "-map_metadata:s:v", "-1",
                "-map_metadata:s:a", "-1",
                "-map_chapters", "-1",
                "-fflags", "+bitexact",
                "-flags:v", "+bitexact",
                "-flags:a", "+bitexact",
                "-movflags", "+faststart",
                str(out)
            ]

        logger.info(f"Executing FFmpeg render ({len(valid_intervals)} segments, framing: {mode}, blur: {r}px, duration: {duration:.1f}s, subtitles: {burn_captions})")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()


        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="ignore")
            logger.warning(f"FFmpeg render error: {err_msg[:250]}. Retrying fallback...")
            # Fallback simple crop render
            fallback_s = valid_intervals[0][0]
            fallback_e = valid_intervals[-1][1]
            fallback_dur = max(1.0, fallback_e - fallback_s)
            fallback_cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", f"{fallback_s:.3f}",
                "-i", str(src),
                "-t", f"{fallback_dur:.3f}",
                "-vf", f"scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                "-map_metadata", "-1",
                "-map_metadata:s:v", "-1",
                "-map_metadata:s:a", "-1",
                "-map_chapters", "-1",
                "-fflags", "+bitexact",
                "-flags:v", "+bitexact",
                "-flags:a", "+bitexact",
                "-movflags", "+faststart",
                str(out)
            ]
            fallback_proc = await asyncio.create_subprocess_exec(
                *fallback_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, fallback_err = await fallback_proc.communicate()
            if fallback_proc.returncode != 0:
                raise MediaProcessingError(f"Video rendering failed: {fallback_err.decode('utf-8', errors='ignore')}")

        return out

    async def generate_thumbnail(
        self,
        source_video_path: Path | str,
        timestamp: float,
        output_thumbnail_path: Path | str,
    ) -> Path:
        """Extract a single high-quality frame at the hook timestamp for thumbnail with all metadata stripped."""
        src = Path(source_video_path).resolve()
        out = Path(output_thumbnail_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss", f"{max(0.0, timestamp):.3f}",
            "-i", str(src),
            "-vframes", "1",
            "-q:v", "2",
            "-map_metadata", "-1",
            str(out)
        ]


        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if not out.exists():
            fallback_cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", "0.0",
                "-i", str(src),
                "-vframes", "1",
                "-q:v", "2",
                str(out)
            ]
            fallback_proc = await asyncio.create_subprocess_exec(
                *fallback_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await fallback_proc.communicate()

        return out


renderer = VideoRenderer()
video_renderer = renderer
