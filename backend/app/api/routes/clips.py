"""Clip details, interactive re-trimming, strategic regeneration, and user feedback endpoints."""

import json
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.database import get_db
from app.core.models import ClipCandidate, RenderedClip, Transcript, UserFeedback, Video
from app.core.schemas import (
    CandidateScores,
    ClipEditRequest,
    ClipRegenerateRequest,
    PlatformMetadata,
    RenderedClipResponse,
    UserFeedbackCreate,
)
from app.services.media.captioner import captioner
from app.services.media.reframing import reframer
from app.services.media.renderer import renderer
from app.services.media.silence_detector import silence_detector, TimelineEdit
from app.services.pipeline.regenerator import clip_regenerator
from app.utils.storage import get_media_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clips", tags=["Clips"])



@router.get("", response_model=List[RenderedClipResponse])
async def list_all_clips(
    limit: int = 60,
    mode: str = None,
    favorite_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all globally generated rendered clips across all jobs with filtering."""
    stmt = (
        select(RenderedClip)
        .options(selectinload(RenderedClip.candidate))
        .order_by(RenderedClip.created_at.desc())
        .limit(limit)
    )
    if mode:
        stmt = stmt.where(RenderedClip.mode == mode)
    if favorite_only:
        stmt = stmt.where(RenderedClip.is_favorite == True)

    result = await db.execute(stmt)
    clips = result.scalars().all()

    output = []
    for clip in clips:
        cand = clip.candidate
        scores = CandidateScores(
            hook_score=cand.hook_score if cand else 0.0,
            retention_score=cand.retention_score if cand else 0.0,
            curiosity_score=cand.curiosity_score if cand else 0.0,
            emotion_score=cand.emotion_score if cand else 0.0,
            story_score=cand.story_score if cand else 0.0,
            payoff_score=cand.payoff_score if cand else 0.0,
            shareability_score=cand.shareability_score if cand else 0.0,
            novelty_score=cand.novelty_score if cand else 0.0,
            quotability_score=cand.quotability_score if cand else 0.0,
            standalone_score=cand.standalone_score if cand else 0.0,
            rewatch_score=cand.rewatch_score if cand else 0.0,
            visual_score=cand.visual_score if cand else 0.0,
            audio_score=cand.audio_score if cand else 0.0,
            platform_score=cand.platform_score if cand else 0.0,
            composite_score=cand.composite_score if cand else 0.0,
            penalty_deduction=cand.penalty_deduction if cand else 0.0,
        )

        metadata = PlatformMetadata(
            tiktok_title=clip.tiktok_title or "",
            tiktok_caption=clip.tiktok_caption or "",
            tiktok_hashtags=json.loads(clip.tiktok_hashtags or "[]"),
            reels_caption=clip.reels_caption or "",
            reels_hashtags=json.loads(clip.reels_hashtags or "[]"),
            shorts_title=clip.shorts_title or "",
            shorts_description=clip.shorts_description or "",
            shorts_hashtags=json.loads(clip.shorts_hashtags or "[]"),
        )

        timeline_data = json.loads(clip.timeline_edit_json) if clip.timeline_edit_json else None

        output.append(
            RenderedClipResponse(
                id=clip.id,
                candidate_id=clip.candidate_id,
                job_id=clip.job_id,
                video_id=clip.video_id,
                mode=clip.mode or "podcast",
                video_url=get_media_url(clip.video_path),
                thumbnail_url=get_media_url(clip.thumbnail_path) if clip.thumbnail_path else None,
                srt_url=get_media_url(clip.srt_path) if clip.srt_path else None,
                ass_url=get_media_url(clip.ass_path) if clip.ass_path else None,
                start_time=clip.start_time,
                end_time=clip.end_time,
                duration=clip.duration,
                aspect_ratio=clip.aspect_ratio,
                framing_mode=getattr(clip, "framing_mode", "crop_9_16") or "crop_9_16",
                blur_radius=getattr(clip, "blur_radius", 30) or 30,
                subtitle_position=getattr(clip, "subtitle_position", 75) or 75,
                add_hook_header=getattr(clip, "add_hook_header", False) or False,
                hook_header_position=getattr(clip, "hook_header_position", 12) or 12,
                hook_header_text=getattr(clip, "hook_header_text", None),
                remove_watermark=getattr(clip, "remove_watermark", False) or False,
                watermark_position=getattr(clip, "watermark_position", "top_right") or "top_right",
                enhance_quality=getattr(clip, "enhance_quality", True) if getattr(clip, "enhance_quality", True) is not None else True,
                hook_strategy=getattr(clip, "hook_strategy", "teaser_climax_hook") or "teaser_climax_hook",
                caption_style=clip.caption_style,
                burn_captions=clip.burn_captions,
                timeline_edit=timeline_data,
                scores=scores,
                reason=cand.reason if cand else None,
                hook_text=cand.hook_text if cand else None,
                payoff_text=cand.payoff_text if cand else None,
                metadata=metadata,
                is_favorite=clip.is_favorite,
                is_rejected=clip.is_rejected,
                created_at=clip.created_at,
            )
        )
    return output



@router.get("/{id}", response_model=RenderedClipResponse)
async def get_clip(id: str, db: AsyncSession = Depends(get_db)):

    """Retrieve full clip information, 12-score breakdown, and platform metadata."""
    stmt = (
        select(RenderedClip)
        .where(RenderedClip.id == id)
        .options(selectinload(RenderedClip.candidate))
    )
    result = await db.execute(stmt)
    clip = result.scalar_one_or_none()

    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    cand = clip.candidate
    scores = CandidateScores(
        hook_score=cand.hook_score if cand else 0.0,
        retention_score=cand.retention_score if cand else 0.0,
        curiosity_score=cand.curiosity_score if cand else 0.0,
        emotion_score=cand.emotion_score if cand else 0.0,
        story_score=cand.story_score if cand else 0.0,
        payoff_score=cand.payoff_score if cand else 0.0,
        shareability_score=cand.shareability_score if cand else 0.0,
        novelty_score=cand.novelty_score if cand else 0.0,
        quotability_score=cand.quotability_score if cand else 0.0,
        standalone_score=getattr(cand, "standalone_score", 0.0) if cand else 0.0,
        rewatch_score=getattr(cand, "rewatch_score", 0.0) if cand else 0.0,
        visual_score=cand.visual_score if cand else 0.0,
        audio_score=cand.audio_score if cand else 0.0,
        platform_score=cand.platform_score if cand else 0.0,
        composite_score=cand.composite_score if cand else 0.0,
        penalty_deduction=cand.penalty_deduction if cand else 0.0,
    )

    metadata = PlatformMetadata(
        tiktok_title=clip.tiktok_title or "",
        tiktok_caption=clip.tiktok_caption or "",
        tiktok_hashtags=json.loads(clip.tiktok_hashtags or "[]"),
        reels_caption=clip.reels_caption or "",
        reels_hashtags=json.loads(clip.reels_hashtags or "[]"),
        shorts_title=clip.shorts_title or "",
        shorts_description=clip.shorts_description or "",
        shorts_hashtags=json.loads(clip.shorts_hashtags or "[]"),
    )

    timeline_data = json.loads(clip.timeline_edit_json) if clip.timeline_edit_json else None

    return RenderedClipResponse(
        id=clip.id,
        candidate_id=clip.candidate_id,
        job_id=clip.job_id,
        video_id=clip.video_id,
        mode=clip.mode or "podcast",
        video_url=get_media_url(clip.video_path),
        thumbnail_url=get_media_url(clip.thumbnail_path) if clip.thumbnail_path else None,
        srt_url=get_media_url(clip.srt_path) if clip.srt_path else None,
        ass_url=get_media_url(clip.ass_path) if clip.ass_path else None,
        start_time=clip.start_time,
        end_time=clip.end_time,
        duration=clip.duration,
        aspect_ratio=clip.aspect_ratio,
        framing_mode=getattr(clip, "framing_mode", "crop_9_16") or "crop_9_16",
        blur_radius=getattr(clip, "blur_radius", 30) or 30,
        subtitle_position=getattr(clip, "subtitle_position", 75) or 75,
        add_hook_header=getattr(clip, "add_hook_header", False) or False,
        hook_header_position=getattr(clip, "hook_header_position", 12) or 12,
        hook_header_text=getattr(clip, "hook_header_text", None),
        remove_watermark=getattr(clip, "remove_watermark", False) or False,
        watermark_position=getattr(clip, "watermark_position", "top_right") or "top_right",
        enhance_quality=getattr(clip, "enhance_quality", True) if getattr(clip, "enhance_quality", True) is not None else True,
        hook_strategy=getattr(clip, "hook_strategy", "teaser_climax_hook") or "teaser_climax_hook",
        caption_style=clip.caption_style,
        burn_captions=clip.burn_captions,
        timeline_edit=timeline_data,
        scores=scores,
        reason=cand.reason if cand else None,
        hook_text=cand.hook_text if cand else None,
        payoff_text=cand.payoff_text if cand else None,
        metadata=metadata,
        is_favorite=clip.is_favorite,
        is_rejected=clip.is_rejected,
        created_at=clip.created_at,
    )


@router.post("/{id}/re-render", response_model=RenderedClipResponse)
async def rerender_clip(
    id: str,
    req: ClipEditRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually edit boundaries, hook header, and layout, then re-render clip.
    """
    stmt = (
        select(RenderedClip)
        .where(RenderedClip.id == id)
        .options(selectinload(RenderedClip.candidate))
    )
    result = await db.execute(stmt)
    clip = result.scalar_one_or_none()

    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video = await db.get(Video, clip.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Source video not found")

    video_path = Path(video.file_path)
    start_time = max(0.0, req.start_time)
    end_time = min(video.duration_seconds, req.end_time)

    if end_time <= start_time + 3.0:
        raise HTTPException(status_code=400, detail="Clip duration must be at least 3 seconds.")

    style = req.caption_style or clip.caption_style or "bold_yellow"
    framing = req.framing_mode or getattr(clip, "framing_mode", "crop_9_16") or "crop_9_16"
    blur_r = req.blur_radius if req.blur_radius is not None else getattr(clip, "blur_radius", 30) or 30
    sub_pos = req.subtitle_position if req.subtitle_position is not None else getattr(clip, "subtitle_position", 75) or 75
    add_hook = req.add_hook_header if req.add_hook_header is not None else getattr(clip, "add_hook_header", False)
    hook_pos = req.hook_header_position if req.hook_header_position is not None else (getattr(clip, "hook_header_position", None) or 12)
    hook_txt = req.hook_header_text or getattr(clip, "hook_header_text", None) or (clip.candidate.hook_text if clip.candidate else "") or ""
    remove_wm = req.remove_watermark if req.remove_watermark is not None else getattr(clip, "remove_watermark", False)
    wm_pos = req.watermark_position if req.watermark_position is not None else (getattr(clip, "watermark_position", None) or "top_right")
    enhance = req.enhance_quality if req.enhance_quality is not None else getattr(clip, "enhance_quality", True)
    if enhance is None:
        enhance = True

    # Calculate dead air timeline cuts
    if req.remove_dead_air:
        silence_intervals = await silence_detector.detect_silence(video_path)
        t_edit = silence_detector.build_edited_timeline(start_time, end_time, silence_intervals)
    else:
        t_edit = TimelineEdit(
            source_start=start_time,
            source_end=end_time,
            keep=[[start_time, end_time]],
            dead_air_removed_seconds=0.0,
        )

    final_dur = round(sum(e - s for s, e in t_edit.keep), 2)
    clip.start_time = start_time
    clip.end_time = end_time
    clip.duration = final_dur
    clip.caption_style = style
    clip.burn_captions = req.burn_captions
    clip.framing_mode = framing
    clip.blur_radius = blur_r
    clip.subtitle_position = sub_pos
    clip.add_hook_header = add_hook
    clip.hook_header_position = hook_pos
    clip.hook_header_text = hook_txt if add_hook else None
    clip.remove_watermark = remove_wm
    clip.watermark_position = wm_pos
    clip.enhance_quality = enhance
    clip.aspect_ratio = "16:9" if framing == "original_16_9" else "9:16"
    clip.timeline_edit_json = json.dumps(t_edit.model_dump())

    # Fetch transcript
    t_stmt = select(Transcript).where(Transcript.video_id == video.id)
    t_res = await db.execute(t_stmt)
    transcript = t_res.scalar_one_or_none()
    segments = json.loads(transcript.segments_json) if transcript else []

    ass_path = settings.SUBTITLE_DIR / f"{clip.id}.ass"
    srt_path = settings.SUBTITLE_DIR / f"{clip.id}.srt"
    captioner.generate_ass(
        segments,
        start_time,
        end_time,
        ass_path,
        style=style,
        subtitle_position=sub_pos,
        add_hook_header=add_hook,
        hook_header_text=hook_txt,
        hook_header_position=hook_pos,
        keep_intervals=t_edit.keep,
    )
    captioner.generate_srt(segments, start_time, end_time, srt_path, keep_intervals=t_edit.keep)

    out_video_path = settings.PROCESSED_DIR / f"{clip.id}.mp4"
    crop_info = {"mode": "center_crop"}

    should_burn = req.burn_captions and style != "none"
    await renderer.render_clip(
        source_video_path=video_path,
        start_time=start_time,
        end_time=end_time,
        output_video_path=out_video_path,
        reframing_config=crop_info,
        ass_subtitle_path=ass_path if should_burn else None,
        burn_captions=should_burn,
        keep_intervals=t_edit.keep,
        framing_mode=framing,
        blur_radius=blur_r,
        remove_watermark=remove_wm,
        watermark_position=wm_pos,
        enhance_quality=enhance,
    )

    thumb_path = settings.THUMBNAIL_DIR / f"{clip.id}.jpg"
    await renderer.generate_thumbnail(out_video_path, 1.0, thumb_path)

    # Track manual edit feedback
    db.add(UserFeedback(clip_id=clip.id, action="manually_edited"))

    await db.commit()
    await db.refresh(clip)

    return await get_clip(id, db)


@router.post("/{id}/refresh-thumbnail", response_model=RenderedClipResponse)
async def refresh_thumbnail(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Re-extract a fresh, non-black 9:16 thumbnail frame directly from the rendered clip."""
    stmt = select(RenderedClip).where(RenderedClip.id == id).options(selectinload(RenderedClip.candidate))
    res = await db.execute(stmt)
    clip = res.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    out_video_path = Path(clip.video_path)
    if not out_video_path.exists():
        raise HTTPException(status_code=400, detail="Rendered clip video file does not exist")

    thumb_path = settings.THUMBNAIL_DIR / f"{clip.id}.jpg"
    await renderer.generate_thumbnail(out_video_path, 1.0, thumb_path)
    clip.thumbnail_path = str(thumb_path)
    await db.commit()
    await db.refresh(clip)
    return await get_clip(id, db)


@router.post("/{id}/regenerate", response_model=RenderedClipResponse)
async def regenerate_clip(
    id: str,
    req: ClipRegenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Strategic AI Clip Regeneration (stronger hook, shorter, longer, different payoff)."""
    await clip_regenerator.regenerate_clip(
        session=db,
        clip_id=id,
        intent=req.intent,
        caption_style=req.caption_style,
        custom_note=req.custom_note,
        subtitle_position=req.subtitle_position,
        add_hook_header=req.add_hook_header,
        hook_header_position=req.hook_header_position,
        hook_header_text=req.hook_header_text,
        remove_watermark=req.remove_watermark,
        watermark_position=req.watermark_position,
        enhance_quality=req.enhance_quality,
    )
    # Track feedback
    db.add(UserFeedback(clip_id=id, action="regenerated", feedback_text=req.intent))
    await db.commit()
    return await get_clip(id, db)



@router.post("/{id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    id: str,
    req: UserFeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    """Store human review action (accepted, rejected, favorite, edited) for future learning."""
    clip = await db.get(RenderedClip, id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if req.action == "favorite":
        clip.is_favorite = True
    elif req.action == "rejected":
        clip.is_rejected = True

    feedback = UserFeedback(
        clip_id=id,
        action=req.action,
        feedback_text=req.feedback_text,
        metadata_json=json.dumps(req.metadata or {}),
    )
    db.add(feedback)
    await db.commit()

    return {"status": "success", "message": f"Feedback '{req.action}' recorded."}


@router.post("/{id}/favorite")
async def toggle_favorite(id: str, db: AsyncSession = Depends(get_db)):
    """Toggle clip favorite state."""
    clip = await db.get(RenderedClip, id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    clip.is_favorite = not clip.is_favorite
    action = "favorite" if clip.is_favorite else "unfavorite"
    db.add(UserFeedback(clip_id=id, action=action))
    await db.commit()

    return {"id": clip.id, "is_favorite": clip.is_favorite}


@router.delete("/{id}")
async def delete_clip(id: str, db: AsyncSession = Depends(get_db)):
    """Permanently delete a rendered clip."""
    clip = await db.get(RenderedClip, id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Delete disk files if present
    for p in [clip.video_path, clip.thumbnail_path, clip.srt_path, clip.ass_path]:
        if p and Path(p).exists():
            try:
                Path(p).unlink()
            except Exception:
                pass

    await db.delete(clip)
    await db.commit()

    return {"message": "Clip deleted successfully.", "id": id}


@router.post("/bulk-delete")
async def bulk_delete_clips(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple rendered clips permanently."""
    clip_ids = payload.get("clip_ids", [])
    if not clip_ids:
        return {"deleted_count": 0, "message": "No clips specified"}

    stmt = select(RenderedClip).where(RenderedClip.id.in_(clip_ids))
    res = await db.execute(stmt)
    clips = res.scalars().all()

    for clip in clips:
        for p in [clip.video_path, clip.thumbnail_path, clip.srt_path, clip.ass_path]:
            if p and Path(p).exists():
                try:
                    Path(p).unlink()
                except Exception:
                    pass
        await db.delete(clip)

    await db.commit()
    return {"deleted_count": len(clips), "status": "success"}

