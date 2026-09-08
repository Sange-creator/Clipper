"""Strategic Clip Regeneration Engine implementing user intents."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import ClipNotFoundError
from app.core.models import ClipCandidate, RenderedClip, Transcript, Video
from app.services.ai.factory import get_ai_provider
from app.services.media.captioner import captioner
from app.services.media.reframing import reframer
from app.services.media.renderer import renderer

logger = logging.getLogger(__name__)


class ClipRegeneratorService:
    """Regenerates clips based on user strategic feedback (stronger hook, shorter, longer, etc.)."""

    async def regenerate_clip(
        self,
        session: AsyncSession,
        clip_id: str,
        intent: str,
        caption_style: Optional[str] = None,
        custom_note: Optional[str] = None,
        subtitle_position: Optional[int] = None,
        add_hook_header: Optional[bool] = None,
        hook_header_position: Optional[int] = None,
        hook_header_style: Optional[str] = None,
        hook_header_text: Optional[str] = None,
        remove_watermark: Optional[bool] = None,
        watermark_position: Optional[str] = None,
        enhance_quality: Optional[bool] = None,
        burn_captions: Optional[bool] = None,
        enable_series_parts: Optional[bool] = None,
        add_part_badge: Optional[bool] = None,
        mirror_video: Optional[bool] = None,
        anti_copyright: Optional[bool] = None,
        video_scale: Optional[float] = None,
        video_pan_x: Optional[float] = None,
        video_pan_y: Optional[float] = None,
    ) -> RenderedClip:
        """Apply strategic regeneration adjustments and re-render clip."""
        stmt = (
            select(RenderedClip)
            .where(RenderedClip.id == clip_id)
            .options(selectinload(RenderedClip.candidate))
        )
        res = await session.execute(stmt)
        clip = res.scalar_one_or_none()
        if not clip:
            raise ClipNotFoundError(f"Clip not found: {clip_id}")

        video = await session.get(Video, clip.video_id)
        if not video:
            raise ClipNotFoundError("Associated video source not found.")

        # Load transcript segments
        t_stmt = select(Transcript).where(Transcript.video_id == video.id)
        t_res = await session.execute(t_stmt)
        transcript = t_res.scalar_one_or_none()
        segments = json.loads(transcript.segments_json) if transcript else []

        video_dur = clip.candidate.end - clip.candidate.start if clip.candidate else clip.duration
        start_time = clip.start_time
        end_time = clip.end_time

        # Apply intent transformations
        if intent == "stronger_hook":
            # Snap directly to the nearest punchy hook word and remove fillers
            from app.services.pipeline.context_expansion import context_expansion_service
            snapped = context_expansion_service.snap_to_hook(start_time + 0.8, segments)
            start_time = min(end_time - 5.0, snapped)
        elif intent == "shorter_duration":
            # Trim 15% from end
            dur = end_time - start_time
            end_time = max(start_time + 5.0, end_time - (dur * 0.2))
        elif intent == "longer_context":
            # Expand backwards by 5 seconds
            start_time = max(0.0, start_time - 5.0)
        elif intent == "different_payoff":
            # Extend payoff
            end_time = min(video_dur, end_time + 6.0)

        # Snap to nearest natural word boundary in transcript
        for s in segments:
            if abs(s.get("start", 0.0) - start_time) < 3.0:
                start_time = s.get("start", start_time)
                break
        for s in reversed(segments):
            if abs(s.get("end", 0.0) - end_time) < 3.0:
                end_time = s.get("end", end_time)
                break

        # Re-render assets
        clip.start_time = round(start_time, 2)
        clip.end_time = round(end_time, 2)
        clip.duration = round(end_time - start_time, 2)

        chosen_burn_captions = burn_captions if burn_captions is not None else getattr(clip, "burn_captions", True)
        chosen_enable_parts = enable_series_parts if enable_series_parts is not None else (add_part_badge if add_part_badge is not None else getattr(clip, "enable_series_parts", getattr(clip, "add_part_badge", True)))
        chosen_style = caption_style or clip.caption_style or "bold_yellow"
        chosen_sub_pos = subtitle_position if subtitle_position is not None else getattr(clip, "subtitle_position", 75)
        chosen_add_hook = add_hook_header if add_hook_header is not None else getattr(clip, "add_hook_header", False)
        chosen_hook_pos = hook_header_position if hook_header_position is not None else getattr(clip, "hook_header_position", 12)
        chosen_hook_style = hook_header_style if hook_header_style is not None else getattr(clip, "hook_header_style", "viral_creator")
        chosen_hook_text = hook_header_text if hook_header_text is not None else getattr(clip, "hook_header_text", None)
        chosen_remove_wm = remove_watermark if remove_watermark is not None else getattr(clip, "remove_watermark", False)
        chosen_wm_pos = watermark_position if watermark_position is not None else (getattr(clip, "watermark_position", None) or "top_right")
        chosen_enhance = enhance_quality if enhance_quality is not None else getattr(clip, "enhance_quality", True)
        if chosen_enhance is None:
            chosen_enhance = True

        chosen_mirror = mirror_video if mirror_video is not None else getattr(clip, "mirror_video", False)
        chosen_anti_copy = anti_copyright if anti_copyright is not None else getattr(clip, "anti_copyright", False)
        chosen_scale = video_scale if video_scale is not None else getattr(clip, "video_scale", 1.0)
        chosen_pan_x = video_pan_x if video_pan_x is not None else getattr(clip, "video_pan_x", 0.0)
        chosen_pan_y = video_pan_y if video_pan_y is not None else getattr(clip, "video_pan_y", 0.0)

        clip.caption_style = chosen_style if (chosen_burn_captions and chosen_style) else "none"
        clip.burn_captions = bool(chosen_burn_captions)
        clip.enable_series_parts = bool(chosen_enable_parts)
        clip.add_part_badge = bool(chosen_enable_parts)
        clip.subtitle_position = chosen_sub_pos
        clip.add_hook_header = chosen_add_hook
        clip.hook_header_position = chosen_hook_pos
        clip.hook_header_style = chosen_hook_style
        clip.hook_header_text = chosen_hook_text if chosen_add_hook else None
        clip.remove_watermark = chosen_remove_wm
        clip.watermark_position = chosen_wm_pos
        clip.enhance_quality = chosen_enhance
        clip.mirror_video = bool(chosen_mirror)
        clip.anti_copyright = bool(chosen_anti_copy)
        clip.video_scale = float(chosen_scale or 1.0)
        clip.video_pan_x = float(chosen_pan_x or 0.0)
        clip.video_pan_y = float(chosen_pan_y or 0.0)

        video_path = Path(video.file_path)
        ass_path = settings.SUBTITLE_DIR / f"{clip.id}.ass"
        srt_path = settings.SUBTITLE_DIR / f"{clip.id}.srt"
        out_video_path = settings.PROCESSED_DIR / f"{clip.id}.mp4"
        thumb_path = settings.THUMBNAIL_DIR / f"{clip.id}.jpg"

        # Load existing keep_intervals if present
        keep_intervals = None
        if clip.timeline_edit_json:
            try:
                t_data = json.loads(clip.timeline_edit_json)
                keep_intervals = t_data.get("keep")
            except Exception:
                pass

        should_burn = bool(
            (chosen_burn_captions and chosen_style and chosen_style != "none")
            or (chosen_add_hook and chosen_hook_text)
            or (chosen_enable_parts and clip.part_index)
        )

        # 1. Captions with persistent hook header & part badge
        captioner.generate_ass(
            segments,
            clip.start_time,
            clip.end_time,
            ass_path,
            style=chosen_style,
            subtitle_position=chosen_sub_pos,
            add_hook_header=chosen_add_hook,
            hook_header_text=chosen_hook_text,
            hook_header_position=chosen_hook_pos,
            hook_header_style=chosen_hook_style,
            keep_intervals=keep_intervals,
            part_index=clip.part_index,
            total_parts=clip.total_parts,
            part_badge_position=getattr(clip, "part_badge_position", 6),
            part_badge_align=getattr(clip, "part_badge_align", "center"),
            canvas_background=getattr(clip, "canvas_background", "blur"),
            framing_mode=getattr(clip, "framing_mode", "crop_9_16"),
            add_part_badge=chosen_enable_parts,
            show_subtitles=chosen_burn_captions,
        )
        captioner.generate_srt(
            segments,
            clip.start_time,
            clip.end_time,
            srt_path,
            keep_intervals=keep_intervals,
            part_index=clip.part_index,
            total_parts=clip.total_parts,
        )

        # 2. Reframing & Render
        crop_info = await reframer.calculate_crop_trajectory(video_path, clip.start_time, clip.end_time)
        await renderer.render_clip(
            source_video_path=video_path,
            start_time=clip.start_time,
            end_time=clip.end_time,
            output_video_path=out_video_path,
            reframing_config=crop_info,
            ass_subtitle_path=ass_path if should_burn else None,
            burn_captions=should_burn,
            keep_intervals=keep_intervals,
            framing_mode=getattr(clip, "framing_mode", "crop_9_16"),
            blur_radius=getattr(clip, "blur_radius", 30),
            remove_watermark=chosen_remove_wm,
            watermark_position=chosen_wm_pos,
            enhance_quality=chosen_enhance,
            mirror_video=clip.mirror_video,
            anti_copyright=clip.anti_copyright,
            video_scale=clip.video_scale,
            video_pan_x=clip.video_pan_x,
            video_pan_y=clip.video_pan_y,
        )

        # 3. Thumbnail from rendered vertical video (guarantees 9:16 layout & non-black frame)
        await renderer.generate_thumbnail(out_video_path, 1.0, thumb_path)

        # 4. Update metadata if custom note
        if custom_note:
            ai = get_ai_provider()
            clip_text = " ".join([s.get("text", "") for s in segments if s.get("end", 0) >= clip.start_time and s.get("start", 0) <= clip.end_time])
            new_meta = await ai.generate_metadata(clip_text, {"hook_summary": custom_note, "payoff_summary": "Regenerated clip"})
            clip.tiktok_title = new_meta.tiktok_title
            clip.tiktok_caption = new_meta.tiktok_caption
            clip.tiktok_hashtags = json.dumps(new_meta.tiktok_hashtags)

        await session.commit()
        await session.refresh(clip)
        logger.info(f"Clip {clip_id} regenerated with intent '{intent}' ({clip.start_time:.1f}s -> {clip.end_time:.1f}s)")
        return clip


clip_regenerator = ClipRegeneratorService()
