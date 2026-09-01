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

        start_time = clip.start_time
        end_time = clip.end_time
        video_dur = video.duration_seconds

        # Apply intent transformations
        if intent == "stronger_hook":
            # Advance start by 2-3s past any setup or find punchier opening sentence
            start_time = min(end_time - 10.0, start_time + 3.0)
        elif intent == "shorter_duration":
            # Trim 25% from setup, preserving conclusion
            current_dur = end_time - start_time
            if current_dur > 15.0:
                start_time += (current_dur * 0.25)
        elif intent == "longer_context":
            # Expand backwards by 6-8 seconds
            start_time = max(0.0, start_time - 7.0)
        elif intent == "different_payoff":
            # Extend ending to subsequent segment
            end_time = min(video_dur, end_time + 6.0)

        # Snap to transcript segment boundaries
        for s in segments:
            if abs(s.get("start", 0.0) - start_time) < 3.0:
                start_time = s.get("start", start_time)
                break
        for s in reversed(segments):
            if abs(s.get("end", 0.0) - end_time) < 3.0:
                end_time = s.get("end", end_time)
                break

        # Re-render assets
        chosen_style = caption_style or clip.caption_style or "bold_yellow"
        chosen_sub_pos = subtitle_position if subtitle_position is not None else getattr(clip, "subtitle_position", 75)
        clip.start_time = round(start_time, 2)
        clip.end_time = round(end_time, 2)
        clip.duration = round(end_time - start_time, 2)
        clip.caption_style = chosen_style
        clip.subtitle_position = chosen_sub_pos

        video_path = Path(video.file_path)
        ass_path = settings.SUBTITLE_DIR / f"{clip.id}.ass"
        srt_path = settings.SUBTITLE_DIR / f"{clip.id}.srt"
        out_video_path = settings.PROCESSED_DIR / f"{clip.id}.mp4"
        thumb_path = settings.THUMBNAIL_DIR / f"{clip.id}.jpg"

        # 1. Captions
        captioner.generate_ass(segments, clip.start_time, clip.end_time, ass_path, style=chosen_style, subtitle_position=chosen_sub_pos)
        captioner.generate_srt(segments, clip.start_time, clip.end_time, srt_path)

        # 2. Reframing & Render
        crop_info = await reframer.calculate_crop_trajectory(video_path, clip.start_time, clip.end_time)
        await renderer.render_clip(
            source_video_path=video_path,
            start_time=clip.start_time,
            end_time=clip.end_time,
            output_video_path=out_video_path,
            reframing_config=crop_info,
            ass_subtitle_path=ass_path,
            burn_captions=True,
            framing_mode=getattr(clip, "framing_mode", "crop_9_16"),
            blur_radius=getattr(clip, "blur_radius", 30),
        )


        # 3. Thumbnail
        await renderer.generate_thumbnail(video_path, clip.start_time + 1.0, thumb_path)

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
