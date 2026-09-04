"""Project management, multi-video batch upload, and project-wide clipping endpoints."""

import json
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.database import get_db
from app.core.exceptions import ClipperException
from app.core.models import (
    ClipCandidate,
    Job,
    Project,
    RenderedClip,
    UserFeedback,
    Video,
)
from app.core.schemas import (
    BatchUploadResponse,
    BulkClipActionRequest,
    CandidateScores,
    PlatformMetadata,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectProcessRequest,
    RenderedClipResponse,
    VideoInfo,
)
from app.services.jobs.job_manager import job_manager
from app.services.media.inspector import inspector
from app.utils.hashing import compute_file_hash
from app.utils.storage import get_media_url, sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("", response_model=ProjectListItem, status_code=status.HTTP_201_CREATED)
async def create_project(req: ProjectCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new multi-video project workspace."""
    project = Project(
        name=req.name,
        mode=req.mode,
        description=req.description,
        settings_json=json.dumps({
            "mode": req.mode,
        }),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectListItem(
        id=project.id,
        name=project.name,
        mode=project.mode,
        description=project.description,
        video_count=0,
        clips_count=0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("", response_model=List[ProjectListItem])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all project workspaces with video and clip counts."""
    stmt = (
        select(
            Project,
            func.count(Video.id.distinct()).label("v_count"),
        )
        .outerjoin(Video, Video.project_id == Project.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for proj, v_count in rows:
        # Count clips in jobs for this project
        c_stmt = (
            select(func.count(RenderedClip.id))
            .join(Job, RenderedClip.job_id == Job.id)
            .where(Job.project_id == proj.id)
        )
        c_res = await db.execute(c_stmt)
        c_count = c_res.scalar() or 0

        items.append(
            ProjectListItem(
                id=proj.id,
                name=proj.name,
                mode=proj.mode or "podcast",
                description=proj.description,
                video_count=v_count,
                clips_count=c_count,
                created_at=proj.created_at,
                updated_at=proj.updated_at,
            )
        )
    return items


@router.get("/{id}", response_model=ProjectDetailResponse)
async def get_project(id: str, db: AsyncSession = Depends(get_db)):
    """Get project details, containing all source videos and generated clips."""
    proj = await db.get(Project, id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    v_stmt = select(Video).where(Video.project_id == id).order_by(Video.created_at.desc())
    v_res = await db.execute(v_stmt)
    videos = v_res.scalars().all()

    video_infos = [
        VideoInfo(
            id=v.id,
            project_id=v.project_id,
            filename=v.filename,
            duration_seconds=v.duration_seconds,
            width=v.width,
            height=v.height,
            fps=v.fps,
            video_codec=v.video_codec,
            audio_codec=v.audio_codec,
            file_size_bytes=v.file_size_bytes,
            created_at=v.created_at,
            video_url=get_media_url(v.file_path),
        )
        for v in videos
    ]

    # Clips across project jobs
    c_stmt = (
        select(RenderedClip)
        .join(Job, RenderedClip.job_id == Job.id)
        .where(Job.project_id == id)
        .options(selectinload(RenderedClip.candidate))
        .order_by(RenderedClip.created_at.desc())
    )
    c_res = await db.execute(c_stmt)
    clips = c_res.scalars().all()

    clip_responses = []
    for c in clips:
        cand = c.candidate
        scores = (
            CandidateScores(
                hook_score=cand.hook_score,
                retention_score=cand.retention_score,
                curiosity_score=cand.curiosity_score,
                emotion_score=cand.emotion_score,
                story_score=cand.story_score,
                payoff_score=cand.payoff_score,
                shareability_score=cand.shareability_score,
                novelty_score=cand.novelty_score,
                quotability_score=cand.quotability_score,
                standalone_score=cand.standalone_score,
                rewatch_score=cand.rewatch_score,
                visual_score=cand.visual_score,
                audio_score=cand.audio_score,
                platform_score=cand.platform_score,
                composite_score=cand.composite_score,
                penalty_deduction=cand.penalty_deduction,
            )
            if cand
            else CandidateScores()
        )

        timeline_data = json.loads(c.timeline_edit_json) if c.timeline_edit_json else None

        clip_responses.append(
            RenderedClipResponse(
                id=c.id,
                candidate_id=c.candidate_id,
                job_id=c.job_id,
                video_id=c.video_id,
                mode=c.mode or proj.mode or "podcast",
                video_url=get_media_url(c.video_path),
                thumbnail_url=get_media_url(c.thumbnail_path) if c.thumbnail_path else None,
                srt_url=get_media_url(c.srt_path) if c.srt_path else None,
                ass_url=get_media_url(c.ass_path) if c.ass_path else None,
                start_time=c.start_time,
                end_time=c.end_time,
                duration=c.duration,
                aspect_ratio=c.aspect_ratio,
                framing_mode=getattr(c, "framing_mode", "crop_9_16") or "crop_9_16",
                blur_radius=getattr(c, "blur_radius", 30) or 30,
                subtitle_position=getattr(c, "subtitle_position", 75) or 75,
                add_hook_header=getattr(c, "add_hook_header", False) or False,
                hook_header_position=getattr(c, "hook_header_position", 12) or 12,
                hook_header_style=getattr(c, "hook_header_style", "viral_creator") or "viral_creator",
                hook_header_text=getattr(c, "hook_header_text", None),
                remove_watermark=getattr(c, "remove_watermark", False) or False,
                watermark_position=getattr(c, "watermark_position", "top_right") or "top_right",
                enhance_quality=getattr(c, "enhance_quality", True) if getattr(c, "enhance_quality", True) is not None else True,
                caption_style=c.caption_style,
                burn_captions=c.burn_captions,
                timeline_edit=timeline_data,
                scores=scores,
                reason=cand.reason if cand else None,
                hook_text=cand.hook_text if cand else None,
                payoff_text=cand.payoff_text if cand else None,
                metadata=PlatformMetadata(
                    tiktok_title=c.tiktok_title or "",
                    tiktok_caption=c.tiktok_caption or "",
                    tiktok_hashtags=json.loads(c.tiktok_hashtags or "[]"),
                    reels_caption=c.reels_caption or "",
                    reels_hashtags=json.loads(c.reels_hashtags or "[]"),
                    shorts_title=c.shorts_title or "",
                    shorts_description=c.shorts_description or "",
                    shorts_hashtags=json.dumps(c.shorts_hashtags or "[]") if isinstance(c.shorts_hashtags, list) else json.loads(c.shorts_hashtags or "[]"),
                ),
                is_favorite=c.is_favorite,
                is_rejected=c.is_rejected,
                created_at=c.created_at,
            )
        )

    return ProjectDetailResponse(
        id=proj.id,
        name=proj.name,
        mode=proj.mode or "podcast",
        description=proj.description,
        videos=video_infos,
        clips=clip_responses,
        total_videos=len(video_infos),
        total_clips=len(clip_responses),
        created_at=proj.created_at,
        updated_at=proj.updated_at,
    )


@router.post("/{id}/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_videos(
    id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch Upload (20–30+ files):
    Validates, computes stable SHA-256 hashes, detects duplicates, and assigns videos to project.
    """
    proj = await db.get(Project, id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    uploaded_videos: List[VideoInfo] = []
    duplicates_count = 0
    failed_count = 0

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for upload_file in files:
        try:
            filename = sanitize_filename(upload_file.filename or "video.mp4")
            temp_path = settings.UPLOAD_DIR / f"temp_{filename}"

            with open(temp_path, "wb") as f:
                while chunk := await upload_file.read(1024 * 1024):
                    f.write(chunk)

            content_hash = compute_file_hash(temp_path)

            # Check duplicate
            stmt = select(Video).where(Video.content_hash == content_hash)
            existing = (await db.execute(stmt)).scalar_one_or_none()

            if existing:
                temp_path.unlink(missing_ok=True)
                existing.project_id = id
                await db.commit()
                duplicates_count += 1
                uploaded_videos.append(
                    VideoInfo(
                        id=existing.id,
                        project_id=id,
                        filename=existing.filename,
                        duration_seconds=existing.duration_seconds,
                        width=existing.width,
                        height=existing.height,
                        fps=existing.fps,
                        video_codec=existing.video_codec,
                        audio_codec=existing.audio_codec,
                        file_size_bytes=existing.file_size_bytes,
                        created_at=existing.created_at,
                        video_url=get_media_url(existing.file_path),
                    )
                )
                continue

            metadata = await inspector.inspect(temp_path)
            target_path = settings.UPLOAD_DIR / f"{content_hash}_{filename}"
            temp_path.rename(target_path)

            video = Video(
                project_id=id,
                content_hash=content_hash,
                filename=filename,
                file_path=str(target_path),
                duration_seconds=metadata.duration_seconds,
                width=metadata.width,
                height=metadata.height,
                fps=metadata.fps,
                video_codec=metadata.video_codec,
                audio_codec=metadata.audio_codec,
                bitrate=metadata.bitrate,
                file_size_bytes=metadata.file_size_bytes,
            )
            db.add(video)
            await db.commit()
            await db.refresh(video)

            uploaded_videos.append(
                VideoInfo(
                    id=video.id,
                    project_id=id,
                    filename=video.filename,
                    duration_seconds=video.duration_seconds,
                    width=video.width,
                    height=video.height,
                    fps=video.fps,
                    video_codec=video.video_codec,
                    audio_codec=video.audio_codec,
                    file_size_bytes=video.file_size_bytes,
                    created_at=video.created_at,
                    video_url=get_media_url(video.file_path),
                )
            )

        except Exception as e:
            logger.exception(f"Failed uploading file in batch: {e}")
            failed_count += 1

    return BatchUploadResponse(
        uploaded_videos=uploaded_videos,
        duplicates_count=duplicates_count,
        failed_count=failed_count,
        total_processed=len(files),
        message=f"Processed {len(files)} videos ({len(uploaded_videos)} active, {duplicates_count} duplicates, {failed_count} failed).",
    )


@router.post("/{id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_project(
    id: str,
    req: ProjectProcessRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers cross-video global candidate discovery and ranking across all project videos.
    """
    proj = await db.get(Project, id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    v_stmt = select(Video).where(Video.project_id == id)
    v_res = await db.execute(v_stmt)
    videos = v_res.scalars().all()

    mode = req.mode or proj.mode or "podcast"
    job = Job(
        project_id=id,
        mode=mode,
        burn_captions=req.burn_captions,
        remove_dead_air=req.remove_dead_air,
        framing_mode=req.framing_mode,
        blur_radius=req.blur_radius,
        subtitle_position=req.subtitle_position,
        add_hook_header=req.add_hook_header,
        hook_header_position=req.hook_header_position,
        hook_header_style=getattr(req, "hook_header_style", "viral_creator") or "viral_creator",
        remove_watermark=req.remove_watermark,
        watermark_position=req.watermark_position,
        enhance_quality=req.enhance_quality,
        status="queued",
        current_stage=1,
        stage_name="Validate project videos",
        config_json=json.dumps({
            "mode": mode,
            "target_clips_count": req.target_clips_count,
            "duration_preset": req.duration_preset,
            "caption_style": req.caption_style,
            "burn_captions": req.burn_captions,
            "remove_dead_air": req.remove_dead_air,
            "framing_mode": req.framing_mode,
            "blur_radius": req.blur_radius,
            "subtitle_position": req.subtitle_position,
            "add_hook_header": req.add_hook_header,
            "hook_header_position": req.hook_header_position,
            "hook_header_style": getattr(req, "hook_header_style", "viral_creator") or "viral_creator",
            "remove_watermark": req.remove_watermark,
            "watermark_position": req.watermark_position,
            "enhance_quality": req.enhance_quality,
            "reframing_mode": req.reframing_mode,
            "ai_provider": req.ai_provider,
            "source_diversity_weight": req.source_diversity_weight,
            "custom_instructions": req.custom_instructions,
        }),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch to background executor
    await job_manager.dispatch_job(job.id)

    return {"job_id": job.id, "status": "queued", "message": "Project processing job queued successfully."}


@router.post("/{id}/bulk-action")
async def bulk_clip_action(
    id: str,
    req: BulkClipActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Applies bulk actions to multiple clips (apply style, favorite, reject, delete)."""
    stmt = select(RenderedClip).where(RenderedClip.id.in_(req.clip_ids))
    res = await db.execute(stmt)
    clips = res.scalars().all()

    for clip in clips:
        if req.action == "favorite":
            clip.is_favorite = True
            db.add(UserFeedback(clip_id=clip.id, action="favorite"))
        elif req.action == "reject":
            clip.is_rejected = True
            db.add(UserFeedback(clip_id=clip.id, action="rejected"))
        elif req.action == "apply_style" and req.caption_style:
            clip.caption_style = req.caption_style

    await db.commit()
    return {"affected_clips": len(clips), "action": req.action, "status": "success"}


@router.delete("/{id}")
async def delete_project(id: str, db: AsyncSession = Depends(get_db)):
    """Delete a single project workspace and cascade all its jobs, clips, and candidate records."""
    proj = await db.get(Project, id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find jobs for this project
    j_stmt = select(Job).where(Job.project_id == id)
    j_res = await db.execute(j_stmt)
    jobs = j_res.scalars().all()
    job_ids = [j.id for j in jobs]

    if job_ids:
        # Delete rendered clips
        cl_stmt = select(RenderedClip).where(RenderedClip.job_id.in_(job_ids))
        cl_res = await db.execute(cl_stmt)
        for cl in cl_res.scalars().all():
            await db.delete(cl)

        # Delete clip candidates
        cand_stmt = select(ClipCandidate).where(ClipCandidate.job_id.in_(job_ids))
        cand_res = await db.execute(cand_stmt)
        for cand in cand_res.scalars().all():
            await db.delete(cand)

        # Delete jobs
        for j in jobs:
            await db.delete(j)

    # Disassociate videos or delete videos assigned to project
    v_stmt = select(Video).where(Video.project_id == id)
    v_res = await db.execute(v_stmt)
    for v in v_res.scalars().all():
        await db.delete(v)

    # Delete project
    await db.delete(proj)
    await db.commit()

    return {"message": "Project workspace deleted successfully.", "id": id}


@router.post("/bulk-delete")
async def bulk_delete_projects(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple project workspaces and their contents."""
    project_ids = payload.get("project_ids", [])
    if not project_ids:
        return {"deleted_count": 0, "message": "No projects specified"}

    # Find projects
    p_stmt = select(Project).where(Project.id.in_(project_ids))
    p_res = await db.execute(p_stmt)
    projects = p_res.scalars().all()

    # Find jobs for these projects
    j_stmt = select(Job).where(Job.project_id.in_(project_ids))
    j_res = await db.execute(j_stmt)
    jobs = j_res.scalars().all()
    job_ids = [j.id for j in jobs]

    if job_ids:
        # Delete rendered clips
        cl_stmt = select(RenderedClip).where(RenderedClip.job_id.in_(job_ids))
        cl_res = await db.execute(cl_stmt)
        for cl in cl_res.scalars().all():
            await db.delete(cl)

        # Delete clip candidates
        cand_stmt = select(ClipCandidate).where(ClipCandidate.job_id.in_(job_ids))
        cand_res = await db.execute(cand_stmt)
        for cand in cand_res.scalars().all():
            await db.delete(cand)

        # Delete jobs
        for j in jobs:
            await db.delete(j)

    # Delete videos
    v_stmt = select(Video).where(Video.project_id.in_(project_ids))
    v_res = await db.execute(v_stmt)
    for v in v_res.scalars().all():
        await db.delete(v)

    # Delete projects
    for p in projects:
        await db.delete(p)

    await db.commit()
    return {"deleted_count": len(projects), "status": "success"}

