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


import re

def slugify_title(title: str, max_len: int = 40) -> str:
    """Generate a clean filesystem slug from a title string."""
    if not title:
        return "short"
    clean = re.sub(r"[^\w\s-]", "", title).strip()
    clean = re.sub(r"[-\s]+", "_", clean)
    return clean[:max_len].strip("_") or "short"


def build_title_text_content(cl: RenderedClip, idx: int) -> str:
    """Format a clean, creator-ready title & caption text document."""
    tt_tags = json.loads(cl.tiktok_hashtags or "[]")
    reels_tags = json.loads(cl.reels_hashtags or "[]")
    shorts_tags = json.loads(cl.shorts_hashtags or "[]")
    all_tags = list(dict.fromkeys(tt_tags + reels_tags + shorts_tags))
    tag_str = " ".join([f"#{t.lstrip('#')}" for t in all_tags]) if all_tags else ""

    title_main = cl.hook_header_text or cl.tiktok_title or cl.shorts_title or f"Viral Clip {idx:02d}"

    return (
        f"==================================================\n"
        f"CLIP {idx:02d}: {title_main}\n"
        f"==================================================\n\n"
        f"[HOOK TITLE]\n"
        f"{title_main}\n\n"
        f"[TIKTOK / REELS CAPTION]\n"
        f"{cl.tiktok_caption or cl.reels_caption or ''}\n\n"
        f"[HASHTAGS]\n"
        f"{tag_str}\n\n"
        f"[YOUTUBE SHORTS TITLE]\n"
        f"{cl.shorts_title or title_main}\n\n"
        f"[DESCRIPTION]\n"
        f"{cl.shorts_description or ''}\n"
    )


@router.get("/job/{job_id}/batch")
async def export_job_batch_package(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Export all rendered clips in a job as a batch ZIP.
    Strictly organized into TWO folders only:
    1. 'videos/' — contains ONLY the rendered .mp4 video files.
    2. 'titles_and_thumbnails/' — contains ONLY thumbnails and title text files.
    """
    stmt = select(RenderedClip).where(RenderedClip.job_id == job_id)
    res = await db.execute(stmt)
    clips = res.scalars().all()

    if not clips:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rendered clips found for this job.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, cl in enumerate(clips, start=1):
            title_hint = cl.hook_header_text or cl.tiktok_title or cl.shorts_title or f"clip_{idx:02d}"
            slug = slugify_title(title_hint)
            base_name = f"clip_{idx:02d}_{cl.id[:6]}_{slug}"

            # Folder 1: videos/ (ONLY .mp4 files)
            if cl.video_path and Path(cl.video_path).exists():
                zf.write(cl.video_path, arcname=f"videos/{base_name}.mp4")

            # Folder 2: titles_and_thumbnails/ (ONLY thumbnails, title txt, and metadata)
            if cl.thumbnail_path and Path(cl.thumbnail_path).exists():
                zf.write(cl.thumbnail_path, arcname=f"titles_and_thumbnails/{base_name}_thumbnail.jpg")

            # Title & captions text file
            txt_content = build_title_text_content(cl, idx)
            zf.writestr(f"titles_and_thumbnails/{base_name}_title.txt", txt_content)

            # Structured platform metadata
            meta_dict = {
                "rank": idx,
                "clip_id": cl.id,
                "duration": cl.duration,
                "hook_title": cl.hook_header_text or cl.tiktok_title,
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
            zf.writestr(f"titles_and_thumbnails/{base_name}_metadata.json", json.dumps(meta_dict, indent=2))

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
    """
    Export a custom list of selected clip IDs as a bulk ZIP bundle.
    Strictly organized into TWO folders only:
    1. 'videos/' — contains ONLY the rendered .mp4 video files.
    2. 'titles_and_thumbnails/' — contains ONLY thumbnails and title text files.
    """
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
            title_hint = cl.hook_header_text or cl.tiktok_title or cl.shorts_title or f"clip_{idx:02d}"
            slug = slugify_title(title_hint)
            base_name = f"clip_{idx:02d}_{cl.id[:6]}_{slug}"

            # Folder 1: videos/ (ONLY .mp4 files)
            if cl.video_path and Path(cl.video_path).exists():
                zf.write(cl.video_path, arcname=f"videos/{base_name}.mp4")

            # Folder 2: titles_and_thumbnails/ (ONLY thumbnails, title txt, and metadata)
            if cl.thumbnail_path and Path(cl.thumbnail_path).exists():
                zf.write(cl.thumbnail_path, arcname=f"titles_and_thumbnails/{base_name}_thumbnail.jpg")

            # Title & captions text file
            txt_content = build_title_text_content(cl, idx)
            zf.writestr(f"titles_and_thumbnails/{base_name}_title.txt", txt_content)

            # Structured platform metadata
            meta_dict = {
                "rank": idx,
                "clip_id": cl.id,
                "duration": cl.duration,
                "hook_title": cl.hook_header_text or cl.tiktok_title,
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
            zf.writestr(f"titles_and_thumbnails/{base_name}_metadata.json", json.dumps(meta_dict, indent=2))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=selected_clips_{len(clips)}_batch.zip"},
    )
