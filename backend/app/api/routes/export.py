"""Export and download endpoints for rendered clips, subtitles, and metadata packages."""

import io
import json
import zipfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import Job, RenderedClip

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/clip/{clip_id}/mp4")
async def export_single_mp4(
    clip_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Directly download the single rendered MP4 9:16 vertical video file."""
    cl = await db.get(RenderedClip, clip_id)
    if not cl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found.")

    if not cl.video_path or not Path(cl.video_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on disk.")

    filename = f"clip_{cl.id[:8]}_{cl.mode or 'short'}.mp4"
    return FileResponse(
        path=cl.video_path,
        media_type="video/mp4",
        filename=filename,
    )


@router.get("/clip/{clip_id}")
async def export_single_clip_package(
    clip_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Export a ZIP bundle containing the MP4 video, ASS subtitle, SRT subtitle, and platform JSON metadata."""
    cl = await db.get(RenderedClip, clip_id)
    if not cl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add MP4
        if cl.video_path and Path(cl.video_path).exists():
            zf.write(cl.video_path, arcname=f"clip_{clip_id[:8]}.mp4")
        # Add Thumbnail
        if cl.thumbnail_path and Path(cl.thumbnail_path).exists():
            zf.write(cl.thumbnail_path, arcname=f"thumbnail_{clip_id[:8]}.jpg")
        # Add ASS
        if cl.ass_path and Path(cl.ass_path).exists():
            zf.write(cl.ass_path, arcname=f"captions_{clip_id[:8]}.ass")
        # Add SRT
        if cl.srt_path and Path(cl.srt_path).exists():
            zf.write(cl.srt_path, arcname=f"captions_{clip_id[:8]}.srt")

        # Metadata JSON
        meta_dict = {
            "clip_id": cl.id,
            "duration": cl.duration,
            "start_time": cl.start_time,
            "end_time": cl.end_time,
            "tiktok": {
                "title": cl.tiktok_title,
                "caption": cl.tiktok_caption,
                "hashtags": json.loads(cl.tiktok_hashtags or "[]"),
            },
            "instagram_reels": {
                "caption": cl.reels_caption,
                "hashtags": json.loads(cl.reels_hashtags or "[]"),
            },
            "youtube_shorts": {
                "title": cl.shorts_title,
                "description": cl.shorts_description,
                "hashtags": json.loads(cl.shorts_hashtags or "[]"),
            },
        }
        zf.writestr("metadata.json", json.dumps(meta_dict, indent=2))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=clip_{clip_id[:8]}_package.zip"},
    )


@router.get("/job/{job_id}/batch")
async def export_job_batch_package(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Export all rendered clips in a job as a batch ZIP."""
    stmt = select(RenderedClip).where(RenderedClip.job_id == job_id)
    res = await db.execute(stmt)
    clips = res.scalars().all()

    if not clips:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rendered clips found for this job.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, cl in enumerate(clips, start=1):
            prefix = f"clip_{idx:02d}_{cl.id[:6]}"
            if cl.video_path and Path(cl.video_path).exists():
                zf.write(cl.video_path, arcname=f"{prefix}/{prefix}.mp4")
            if cl.thumbnail_path and Path(cl.thumbnail_path).exists():
                zf.write(cl.thumbnail_path, arcname=f"{prefix}/{prefix}_thumb.jpg")
            if cl.ass_path and Path(cl.ass_path).exists():
                zf.write(cl.ass_path, arcname=f"{prefix}/{prefix}.ass")
            if cl.srt_path and Path(cl.srt_path).exists():
                zf.write(cl.srt_path, arcname=f"{prefix}/{prefix}.srt")

            meta_dict = {
                "rank": idx,
                "clip_id": cl.id,
                "duration": cl.duration,
                "tiktok": {
                    "title": cl.tiktok_title,
                    "caption": cl.tiktok_caption,
                    "hashtags": json.loads(cl.tiktok_hashtags or "[]"),
                },
                "instagram_reels": {
                    "caption": cl.reels_caption,
                    "hashtags": json.loads(cl.reels_hashtags or "[]"),
                },
                "youtube_shorts": {
                    "title": cl.shorts_title,
                    "description": cl.shorts_description,
                    "hashtags": json.loads(cl.shorts_hashtags or "[]"),
                },
            }
            zf.writestr(f"{prefix}/metadata.json", json.dumps(meta_dict, indent=2))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id[:8]}_all_clips.zip"},
    )


@router.post("/clips/batch")
async def export_custom_clips_batch(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Export a custom list of selected clip IDs as a bulk ZIP bundle."""
    clip_ids = payload.get("clip_ids", [])
    if not clip_ids:
        raise HTTPException(status_code=400, detail="No clip IDs provided.")

    stmt = select(RenderedClip).where(RenderedClip.id.in_(clip_ids))
    res = await db.execute(stmt)
    clips = res.scalars().all()

    if not clips:
        raise HTTPException(status_code=404, detail="No matching clips found.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, cl in enumerate(clips, start=1):
            prefix = f"clip_{idx:02d}_{cl.id[:6]}"
            if cl.video_path and Path(cl.video_path).exists():
                zf.write(cl.video_path, arcname=f"{prefix}/{prefix}.mp4")
            if cl.thumbnail_path and Path(cl.thumbnail_path).exists():
                zf.write(cl.thumbnail_path, arcname=f"{prefix}/{prefix}_thumb.jpg")
            if cl.ass_path and Path(cl.ass_path).exists():
                zf.write(cl.ass_path, arcname=f"{prefix}/{prefix}.ass")
            if cl.srt_path and Path(cl.srt_path).exists():
                zf.write(cl.srt_path, arcname=f"{prefix}/{prefix}.srt")

            meta_dict = {
                "clip_id": cl.id,
                "duration": cl.duration,
                "tiktok": {
                    "title": cl.tiktok_title,
                    "caption": cl.tiktok_caption,
                    "hashtags": json.loads(cl.tiktok_hashtags or "[]"),
                },
                "instagram_reels": {
                    "caption": cl.reels_caption,
                    "hashtags": json.loads(cl.reels_hashtags or "[]"),
                },
                "youtube_shorts": {
                    "title": cl.shorts_title,
                    "description": cl.shorts_description,
                    "hashtags": json.loads(cl.shorts_hashtags or "[]"),
                },
            }
            zf.writestr(f"{prefix}/metadata.json", json.dumps(meta_dict, indent=2))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=selected_clips_{len(clips)}_batch.zip"},
    )
