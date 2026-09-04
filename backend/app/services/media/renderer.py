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


METADATA_STRIP_ARGS = [
    "-map_metadata", "-1",
    "-map_metadata:s:v", "-1",
    "-map_metadata:s:a", "-1",
    "-map_chapters", "-1",
    "-metadata", "title=",
    "-metadata", "artist=",
    "-metadata", "album=",
    "-metadata", "composer=",
    "-metadata", "comment=",
    "-metadata", "description=",
    "-metadata", "synopsis=",
    "-metadata", "author=",
    "-metadata", "date=",
    "-metadata", "creation_time=",
    "-metadata", "handler_name=",
    "-metadata", "encoder=",
    "-metadata", "copyright=",
    "-metadata:s:v", "handler_name=",
    "-metadata:s:v", "title=",
    "-metadata:s:v", "language=",
    "-metadata:s:a", "handler_name=",
    "-metadata", "vendor_id=",
    "-metadata", "compatible_brands=",
    "-metadata", "minor_version=",
    "-metadata", "major_brand=",
    "-metadata:s:v", "handler_name=",
    "-metadata:s:v", "title=",
    "-metadata:s:v", "language=",
    "-metadata:s:v", "encoder=",
    "-metadata:s:a", "handler_name=",
    "-metadata:s:a", "title=",
    "-metadata:s:a", "language=",
    "-metadata:s:a", "encoder=",
    "-fflags", "+bitexact",
    "-flags:v", "+bitexact",
    "-flags:a", "+bitexact",
    "-write_id3v2", "0",
    "-write_id3v1", "0",
]


def get_delogo_filter(position: str = "top_right", width: int = 1920, height: int = 1080) -> str:
    """
    Generate safe delogo filter coordinates to cleanly remove watermarks/logos without edge artifacts.
    Supports individual corners, TikTok bouncing watermarks (top-left & bottom-right), and all corners.
    """
    pos = (position or "top_right").lower().strip()
    box_w = max(40, int(width * 0.13))
    box_h = max(30, int(height * 0.085))
    margin_x = max(10, int(width * 0.015))
    margin_y = max(10, int(height * 0.02))

    def _calc_delogo(corner: str) -> str:
        if corner in ("top_left", "tl"):
            x = margin_x
            y = margin_y
        elif corner in ("bottom_left", "bl"):
            x = margin_x
            y = max(1, height - box_h - margin_y)
        elif corner in ("bottom_right", "br"):
            x = max(1, width - box_w - margin_x)
            y = max(1, height - box_h - margin_y)
        else:  # top_right (default)
            x = max(1, width - box_w - margin_x)
            y = margin_y
        # FFmpeg delogo requires x>=1, y>=1, x+w<=width-1, y+h<=height-1
        safe_x = max(1, min(x, width - box_w - 2))
        safe_y = max(1, min(y, height - box_h - 2))
        return f"delogo=x={safe_x}:y={safe_y}:w={box_w}:h={box_h}:show=0"

    if pos in ("tiktok_bounce", "both_corners", "tiktok"):
        return f"{_calc_delogo('top_left')},{_calc_delogo('bottom_right')}"
    elif pos in ("all_corners", "all"):
        return f"{_calc_delogo('top_left')},{_calc_delogo('top_right')},{_calc_delogo('bottom_left')},{_calc_delogo('bottom_right')}"
    else:
        return _calc_delogo(pos)


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
        remove_watermark: bool = False,
        watermark_position: str = "top_right",
        enhance_quality: bool = True,
        retime_subtitles: bool = False,
    ) -> Path:
        """
        Renders a short-form video clip from source:
        - Accurately cuts between start_time and end_time (or slices multiple keep_intervals).
        - Optional logo/watermark removal before reframing.
        - Applies selected framing mode:
            * crop_9_16: Full 9:16 vertical crop (TikTok / Reels / Shorts default)
            * blur_fit_9_16: 16:9 video centered within 9:16 vertical canvas with customized blurred background
            * original_16_9: Native 16:9 landscape widescreen
        - Optional studio visual enhancement (unsharp edge sharpening, color vibrancy, contrast boost).
        - Burns in styled ASS subtitles if burn_captions is True.
        - Normalizes audio loudness (loudnorm).
        - Fully sanitizes and wipes all original video/container metadata.
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

        # Inspect source resolution if watermark removal is active
        src_w, src_h = 1920, 1080
        if remove_watermark:
            try:
                from app.services.media.inspector import inspector
                meta = await inspector.inspect(src)
                if meta.width > 0 and meta.height > 0:
                    src_w, src_h = meta.width, meta.height
            except Exception:
                pass

        # Subtitle handling
        final_ass_path: Optional[Path] = None
        if burn_captions and ass_subtitle_path:
            p = Path(ass_subtitle_path).resolve()
            if p.exists():
                if len(valid_intervals) > 1 and retime_subtitles:
                    # Retime subtitles to match spliced timeline
                    retimed_content = retime_ass_subtitles(p.read_text(encoding="utf-8"), valid_intervals)
                    retimed_path = p.with_name(f"{p.stem}_retimed.ass")
                    retimed_path.write_text(retimed_content, encoding="utf-8")
                    final_ass_path = retimed_path
                else:
                    final_ass_path = p

        # Resolve delogo filter if watermark removal is requested
        delogo_cmd = ""
        if remove_watermark:
            raw_pos = (watermark_position or "auto").lower().strip()
            if raw_pos in ("auto", "automatic", "detect", "auto_detect"):
                try:
                    from app.services.media.watermark_detector import watermark_detector
                    detect_s = valid_intervals[0][0] if valid_intervals else 0.0
                    detect_e = valid_intervals[-1][1] if valid_intervals else 30.0
                    detect_res = await watermark_detector.detect_watermark(
                        src,
                        start_time=detect_s,
                        end_time=detect_e,
                        width=src_w,
                        height=src_h,
                    )
                    if detect_res.detected and detect_res.delogo_filter:
                        delogo_cmd = detect_res.delogo_filter
                        logger.info(f"Auto-watermark detected '{detect_res.position}' (confidence={detect_res.confidence:.2f})")
                    else:
                        logger.info("Auto-watermark detection: No persistent watermark detected on video.")
                except Exception as e:
                    logger.warning(f"Watermark auto-detection encountered error, defaulting to top_right: {e}")
                    delogo_cmd = get_delogo_filter("top_right", src_w, src_h)
            else:
                delogo_cmd = get_delogo_filter(raw_pos, src_w, src_h)

        # Check if single slice or multi-interval concat
        if len(valid_intervals) == 1:
            # Single slice: Fast seek with Lanczos sharp scaling
            s_time = valid_intervals[0][0]
            e_time = valid_intervals[0][1]
            seg_dur = max(0.5, e_time - s_time)

            filter_parts = []
            if delogo_cmd:
                filter_parts.append(delogo_cmd)

            if mode == "blur_fit_9_16":
                prefix = f"{filter_parts[0]}," if filter_parts else ""
                v_filter = (
                    f"{prefix}split=2[bg_raw][fg_raw];"
                    f"[bg_raw]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=bilinear,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT},boxblur={r}:1,drawbox=color=black@0.35:replace=1[bg];"
                    f"[fg_raw]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=decrease:flags=bilinear[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
                )
            elif mode == "original_16_9":
                filter_parts.append("scale=1920:1080:force_original_aspect_ratio=decrease:flags=bilinear")
                v_filter = ",".join(filter_parts)
            else:
                # Default: crop_9_16
                filter_parts.append(f"scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=bilinear,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}")
                v_filter = ",".join(filter_parts)

            # Studio visual quality enhancement (vibrancy + unsharp detail enhancement)
            if enhance_quality:
                v_filter += ",eq=contrast=1.04:saturation=1.08:brightness=0.01,unsharp=lx=3:ly=3:la=0.35:cx=3:cy=3:ca=0.15"

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
                "-preset", "veryfast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "48000",
                *METADATA_STRIP_ARGS,
                "-movflags", "+faststart",
                str(out)
            ]
        else:
            # Multi-segment splicing: Fast seek multi-input with synchronized concat
            input_args = []
            filter_chunks = []
            concat_streams = ""

            for idx, (s, e) in enumerate(valid_intervals):
                dur = max(0.2, e - s)
                input_args.extend(["-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", str(src)])

                # Reframe each input video stream to standard canvas (apply delogo to raw stream if present)
                in_v = f"[{idx}:v]{delogo_cmd}," if delogo_cmd else f"[{idx}:v]"
                if mode == "blur_fit_9_16":
                    filter_chunks.append(
                        f"{in_v}split=2[bg_raw_{idx}][fg_raw_{idx}];"
                        f"[bg_raw_{idx}]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=bilinear,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT},boxblur={r}:1,drawbox=color=black@0.35:replace=1[bg_{idx}];"
                        f"[fg_raw_{idx}]scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=decrease:flags=bilinear[fg_{idx}];"
                        f"[bg_{idx}][fg_{idx}]overlay=(W-w)/2:(H-h)/2,setsar=1[v{idx}]"
                    )
                elif mode == "original_16_9":
                    filter_chunks.append(
                        f"{in_v}scale=1920:1080:force_original_aspect_ratio=decrease:flags=bilinear,setsar=1[v{idx}]"
                    )
                else:
                    # Default: crop_9_16
                    filter_chunks.append(
                        f"{in_v}scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=bilinear,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT},setsar=1[v{idx}]"
                    )

                concat_streams += f"[v{idx}][{idx}:a]"

            num_segs = len(valid_intervals)
            filter_chunks.append(
                f"{concat_streams}concat=n={num_segs}:v=1:a=1[vcat][acat]"
            )
            v_cat_target = "[vcat]"

            # Quality enhancement & subtitles
            post_filters = []
            if enhance_quality:
                post_filters.append("eq=contrast=1.04:saturation=1.08:brightness=0.01")
                post_filters.append("unsharp=lx=3:ly=3:la=0.35:cx=3:cy=3:ca=0.15")

            if final_ass_path and final_ass_path.exists():
                escaped_ass = str(final_ass_path).replace("\\", "/").replace(":", "\\:")
                post_filters.append(f"subtitles='{escaped_ass}'")

            if post_filters:
                filter_chunks.append(f"{v_cat_target}{','.join(post_filters)}[vout]")
            else:
                filter_chunks.append(f"{v_cat_target}null[vout]")

            # Audio loudness normalization
            filter_chunks.append("[acat]loudnorm=I=-14:TP=-1.0:LRA=11[aout]")

            full_filter = ";".join(filter_chunks)
            cmd = [
                self.ffmpeg_path,
                "-y",
                *input_args,
                "-filter_complex", full_filter,
                "-map", "[vout]",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level:v", "4.2",
                "-preset", "veryfast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "48000",
                *METADATA_STRIP_ARGS,
                "-movflags", "+faststart",
                str(out)
            ]

        logger.info(f"Executing FFmpeg render ({len(valid_intervals)} segments, framing: {mode}, blur: {r}px, duration: {duration:.1f}s, subtitles: {burn_captions})")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=300.0)
        except (asyncio.CancelledError, asyncio.TimeoutError) as err:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            logger.error(f"FFmpeg render cancelled or timed out (duration: {duration:.1f}s): {err}")
            raise

        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="ignore")
            logger.warning(f"FFmpeg render error: {err_msg[-500:]}. Retrying fallback...")
            # Fallback simple crop render
            fallback_s = min(s for s, e in valid_intervals)
            fallback_e = max(e for s, e in valid_intervals)
            fallback_dur = max(1.0, fallback_e - fallback_s)
            fallback_cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", f"{fallback_s:.3f}",
                "-i", str(src),
                "-t", f"{fallback_dur:.3f}",
                "-vf", f"scale={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}:force_original_aspect_ratio=increase:flags=bilinear,crop={settings.TARGET_WIDTH}:{settings.TARGET_HEIGHT}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                *METADATA_STRIP_ARGS,
                "-movflags", "+faststart",
                str(out)
            ]
            fallback_proc = await asyncio.create_subprocess_exec(
                *fallback_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                _, fallback_err = await asyncio.wait_for(fallback_proc.communicate(), timeout=300.0)
            except (asyncio.CancelledError, asyncio.TimeoutError) as fb_err:
                try:
                    fallback_proc.kill()
                    await fallback_proc.wait()
                except Exception:
                    pass
                raise
            if fallback_proc.returncode != 0:
                raise MediaProcessingError(f"Video rendering failed: {fallback_err.decode('utf-8', errors='ignore')}")

        return out

    async def generate_thumbnail(
        self,
        source_video_path: Path | str,
        timestamp: float = 1.0,
        output_thumbnail_path: Path | str = None,
    ) -> Path:
        """
        Extract a crisp, high-quality, representative non-black frame for thumbnail preview.
        - Uses accurate seeking and FFmpeg's smart thumbnail selector.
        - Evaluates candidate timestamps (e.g. target ts, 1.0s, 1.5s, 0.5s, 2.0s) to prevent black frames or cut artifacts.
        - Strips all container metadata.
        """
        src = Path(source_video_path).resolve()
        out = Path(output_thumbnail_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        vid_dur = 5.0
        try:
            probe_proc = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(src),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            p_out, _ = await probe_proc.communicate()
            if probe_proc.returncode == 0 and p_out.decode().strip():
                d = float(p_out.decode().strip())
                if d > 0.1:
                    vid_dur = d
        except Exception:
            pass

        safe_ts = max(0.05, min(timestamp, max(0.05, vid_dur - 0.2)))
        candidate_timestamps = [
            safe_ts,
            max(0.05, min(1.0, vid_dur * 0.5)),
            max(0.05, min(0.5, vid_dur * 0.25)),
            0.05,
        ]

        seen = set()
        dedup_candidates = []
        for ts in candidate_timestamps:
            r_ts = round(ts, 2)
            if r_ts not in seen:
                seen.add(r_ts)
                dedup_candidates.append(r_ts)

        image_strip_args = [
            "-map_metadata", "-1",
            "-map_chapters", "-1",
        ]

        for ts in dedup_candidates:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", f"{ts:.3f}",
                "-i", str(src),
                "-vf", "thumbnail=8",
                "-vframes", "1",
                "-update", "1",
                "-q:v", "2",
                *image_strip_args,
                str(out)
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

            if out.exists() and out.stat().st_size > 1000:
                return out

        # Direct 1-frame fallback if smart filter produced no output
        fallback_cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss", f"{safe_ts:.3f}",
            "-i", str(src),
            "-vframes", "1",
            "-update", "1",
            "-q:v", "2",
            *image_strip_args,
            str(out)
        ]
        fallback_proc = await asyncio.create_subprocess_exec(
            *fallback_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            await asyncio.wait_for(fallback_proc.communicate(), timeout=30.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            try:
                fallback_proc.kill()
                await fallback_proc.wait()
            except Exception:
                pass
            raise

        return out


renderer = VideoRenderer()
video_renderer = renderer

