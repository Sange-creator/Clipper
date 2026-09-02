"""Job creation, status monitoring, and real-time SSE progress streaming."""

import asyncio
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import ClipCandidate, Job, RenderedClip, Video
from app.core.schemas import (
    CandidateDetail,
    CandidateScores,
    JobCreateRequest,
    JobStatusResponse,
    PlatformMetadata,
    RenderedClipResponse,
)
from app.services.jobs.job_manager import job_manager
from app.services.pipeline.pipeline import pipeline_runner
from app.utils.storage import get_media_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.post("", response_model=JobStatusResponse)
async def create_clipping_job(
    req: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create and start a new 21-stage clipping job."""
    video = await db.get(Video, req.video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    config_dict = req.model_dump()
    db_job = Job(
        video_id=req.video_id,
        project_id=req.project_id,
        mode=req.mode,
        burn_captions=req.burn_captions,
        remove_dead_air=req.remove_dead_air,
        framing_mode=req.framing_mode,
        blur_radius=req.blur_radius,
        subtitle_position=req.subtitle_position or 75,
        add_hook_header=req.add_hook_header,
        hook_header_position=req.hook_header_position or 12,
        remove_watermark=req.remove_watermark,
        watermark_position=req.watermark_position or "top_right",
        enhance_quality=req.enhance_quality if req.enhance_quality is not None else True,
        status="queued",
        current_stage=1,
        stage_name="Validate file",
        progress=0.0,
        config_json=json.dumps(config_dict),
        log_history=json.dumps([]),
    )

    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)


    # Launch async background worker
    job_manager.start_job(db_job.id)

    return JobStatusResponse(
        id=db_job.id,
        video_id=db_job.video_id,
        mode=db_job.mode,
        status=db_job.status,
        current_stage=db_job.current_stage,
        stage_name=db_job.stage_name,
        progress=db_job.progress,
        created_at=db_job.created_at,
        updated_at=db_job.updated_at,
        logs=[],
    )


@router.get("", response_model=List[JobStatusResponse])
async def list_all_jobs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all processing jobs across single videos and projects."""
    stmt = (
        select(Job)
        .options(selectinload(Job.candidates), selectinload(Job.rendered_clips))
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    jobs = res.scalars().all()

    output = []
    for job in jobs:
        logs = json.loads(job.log_history or "[]")
        output.append(
            JobStatusResponse(
                id=job.id,
                project_id=job.project_id,
                video_id=job.video_id,
                mode=job.mode or "podcast",
                status=job.status,
                current_stage=job.current_stage,
                stage_name=job.stage_name,
                progress=job.progress,
                total_candidates_found=len(job.candidates),
                total_clips_rendered=len(job.rendered_clips),
                error_message=job.error_message,
                created_at=job.created_at,
                updated_at=job.updated_at,
                logs=logs,
            )
        )
    return output


@router.get("/{job_id}", response_model=JobStatusResponse)

async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current status, stage progress, and logs for a job."""
    stmt = (
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.candidates), selectinload(Job.rendered_clips))
    )
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    logs = json.loads(job.log_history or "[]")
    return JobStatusResponse(
        id=job.id,
        video_id=job.video_id,
        mode=job.mode or "podcast",
        status=job.status,
        current_stage=job.current_stage,
        stage_name=job.stage_name,
        progress=job.progress,
        total_candidates_found=len(job.candidates),
        total_clips_rendered=len(job.rendered_clips),
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        logs=logs,
    )


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str):
    """Server-Sent Events (SSE) stream for real-time progress updates."""
    queue = pipeline_runner.subscribe(job_id)

    async def event_generator():
        try:
            # Send initial ping
            yield f"data: {json.dumps({'type': 'connected', 'job_id': job_id})}\n\n"
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("status") in ("completed", "failed", "cancelled"):
                    break
        except asyncio.CancelledError:
            pass
        finally:
            pipeline_runner.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{job_id}/candidates", response_model=List[CandidateDetail])
async def get_job_candidates(
    job_id: str,
    selected_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve scored candidates for a job."""
    stmt = select(ClipCandidate).where(ClipCandidate.job_id == job_id)
    if selected_only:
        stmt = stmt.where(ClipCandidate.selected == True)
    stmt = stmt.order_by(ClipCandidate.rank.asc())

    res = await db.execute(stmt)
    candidates = res.scalars().all()

    output: List[CandidateDetail] = []
    for c in candidates:
        scores = CandidateScores(
            hook_score=c.hook_score,
            retention_score=c.retention_score,
            curiosity_score=c.curiosity_score,
            emotion_score=c.emotion_score,
            story_score=c.story_score,
            payoff_score=c.payoff_score,
            shareability_score=c.shareability_score,
            novelty_score=c.novelty_score,
            quotability_score=c.quotability_score,
            standalone_score=c.standalone_score,
            rewatch_score=c.rewatch_score,
            visual_score=c.visual_score,
            audio_score=c.audio_score,
            platform_score=c.platform_score,
            composite_score=c.composite_score,
            penalty_deduction=c.penalty_deduction,
        )
        timeline_data = json.loads(c.timeline_edit_json) if c.timeline_edit_json else None
        output.append(
            CandidateDetail(
                id=c.id,
                job_id=c.job_id,
                video_id=c.video_id,
                start_time=c.start_time,
                end_time=c.end_time,
                duration=c.duration,
                scores=scores,
                rank=c.rank,
                selected=c.selected,
                hook_text=c.hook_text,
                payoff_text=c.payoff_text,
                transcript_text=c.transcript_text,
                timeline_edit=timeline_data,
                reason=c.reason,
            )
        )
    return output


@router.get("/{job_id}/clips", response_model=List[RenderedClipResponse])
async def get_job_clips(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all rendered 9:16 clips for a job."""
    stmt = (
        select(RenderedClip)
        .where(RenderedClip.job_id == job_id)
        .options(selectinload(RenderedClip.candidate))
    )
    res = await db.execute(stmt)
    clips = res.scalars().all()

    output: List[RenderedClipResponse] = []
    for cl in clips:
        cand = cl.candidate
        scores = CandidateScores(
            hook_score=cand.hook_score if cand else 80.0,
            retention_score=cand.retention_score if cand else 80.0,
            curiosity_score=cand.curiosity_score if cand else 80.0,
            emotion_score=cand.emotion_score if cand else 80.0,
            story_score=cand.story_score if cand else 80.0,
            payoff_score=cand.payoff_score if cand else 80.0,
            shareability_score=cand.shareability_score if cand else 80.0,
            novelty_score=cand.novelty_score if cand else 80.0,
            quotability_score=cand.quotability_score if cand else 80.0,
            standalone_score=cand.standalone_score if cand else 80.0,
            rewatch_score=cand.rewatch_score if cand else 75.0,
            visual_score=cand.visual_score if cand else 80.0,
            audio_score=cand.audio_score if cand else 80.0,
            platform_score=cand.platform_score if cand else 80.0,
            composite_score=cand.composite_score if cand else 80.0,
            penalty_deduction=cand.penalty_deduction if cand else 0.0,
        )

        metadata = PlatformMetadata(
            tiktok_title=cl.tiktok_title or "",
            tiktok_caption=cl.tiktok_caption or "",
            tiktok_hashtags=json.loads(cl.tiktok_hashtags or "[]"),
            reels_caption=cl.reels_caption or "",
            reels_hashtags=json.loads(cl.reels_hashtags or "[]"),
            shorts_title=cl.shorts_title or "",
            shorts_description=cl.shorts_description or "",
            shorts_hashtags=json.loads(cl.shorts_hashtags or "[]"),
        )

        timeline_data = json.loads(cl.timeline_edit_json) if cl.timeline_edit_json else None

        output.append(
            RenderedClipResponse(
                id=cl.id,
                candidate_id=cl.candidate_id,
                job_id=cl.job_id,
                video_id=cl.video_id,
                mode=cl.mode or "podcast",
                video_url=get_media_url(cl.video_path) or "",
                thumbnail_url=get_media_url(cl.thumbnail_path),
                srt_url=get_media_url(cl.srt_path),
                ass_url=get_media_url(cl.ass_path),
                start_time=cl.start_time,
                end_time=cl.end_time,
                duration=cl.duration,
                aspect_ratio=cl.aspect_ratio,
                framing_mode=getattr(cl, "framing_mode", "crop_9_16") or "crop_9_16",
                blur_radius=getattr(cl, "blur_radius", 30) or 30,
                subtitle_position=getattr(cl, "subtitle_position", 75) or 75,
                add_hook_header=getattr(cl, "add_hook_header", False) or False,
                hook_header_position=getattr(cl, "hook_header_position", 12) or 12,
                hook_header_text=getattr(cl, "hook_header_text", None),
                remove_watermark=getattr(cl, "remove_watermark", False) or False,
                watermark_position=getattr(cl, "watermark_position", "top_right") or "top_right",
                enhance_quality=getattr(cl, "enhance_quality", True) if getattr(cl, "enhance_quality", True) is not None else True,
                caption_style=cl.caption_style,
                burn_captions=cl.burn_captions,
                timeline_edit=timeline_data,
                scores=scores,
                reason=cand.reason if cand else None,
                hook_text=cand.hook_text if cand else None,
                payoff_text=cand.payoff_text if cand else None,
                metadata=metadata,
                is_favorite=cl.is_favorite,
                is_rejected=cl.is_rejected,
                created_at=cl.created_at,
            )
        )
    return output



@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel an active processing job."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    cancelled = job_manager.cancel_job(job_id)
    job.status = "cancelled"
    await db.commit()
    return {"message": "Job cancelled.", "cancelled": cancelled}


@router.delete("/{job_id}")
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Permanently delete a processing job and its associated rendered clips and candidates."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    # Delete rendered clips
    cl_stmt = select(RenderedClip).where(RenderedClip.job_id == job_id)
    cl_res = await db.execute(cl_stmt)
    for cl in cl_res.scalars().all():
        await db.delete(cl)

    # Delete candidates
    cand_stmt = select(ClipCandidate).where(ClipCandidate.job_id == job_id)
    cand_res = await db.execute(cand_stmt)
    for cand in cand_res.scalars().all():
        await db.delete(cand)

    # Delete job
    await db.delete(job)
    await db.commit()

    return {"message": "Job and its clips deleted successfully.", "id": job_id}

