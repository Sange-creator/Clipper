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
from typing import List, Dict, Any


def slugify_title(title: str, max_len: int = 40) -> str:
    """Generate a clean filesystem slug from a title string."""
    if not title:
        return "short"
    clean = re.sub(r"[^\w\s-]", "", title).strip()
    clean = re.sub(r"[-\s]+", "_", clean)
    return clean[:max_len].strip("_") or "short"


def extract_5_hashtags(cl: RenderedClip) -> List[str]:
    """
    Extract exactly 5 clean, distinct hashtags for a clip,
    prioritizing TikTok, Instagram Reels, and YouTube Shorts metadata.
    """
    def parse_tags(raw):
        if not raw:
            return []
        try:
            val = json.loads(raw)
            if isinstance(val, list):
                return [str(t).strip() for t in val if t]
        except Exception:
            pass
        return []

    collected: List[str] = []
    # Collect tags in priority order: tiktok, reels, shorts
    for raw in [cl.tiktok_hashtags, cl.reels_hashtags, cl.shorts_hashtags]:
        for tag in parse_tags(raw):
            clean = "#" + tag.lstrip("#").strip()
            if clean and clean.lower() not in [c.lower() for c in collected]:
                collected.append(clean)
                if len(collected) == 5:
                    return collected

    # High-retention short-form fallbacks if fewer than 5 exist
    defaults = ["#fyp", "#viral", "#shorts", "#trending", "#storytime", "#foryou", "#mindset", "#reels"]
    for d in defaults:
        if len(collected) >= 5:
            break
        if d.lower() not in [c.lower() for c in collected]:
            collected.append(d)

    return collected[:5]


def build_batch_titles_and_hashtags_text(clips_summary: List[Dict[str, Any]]) -> str:
    """
    Generate a single, beautifully formatted text file containing the titles
    and exactly 5 hashtags for all videos in a batch, optimized for 1-click copy-pasting.
    """
    lines = [
        "================================================================================",
        "AI VIDEO CLIPPER — ALL TITLES & 5 HASHTAGS (READY TO COPY & PASTE)",
        "================================================================================",
        f"Total Videos: {len(clips_summary)}",
        "Quick Tip: Select any title or 5-hashtag line below to paste directly into",
        "TikTok, Instagram Reels, or YouTube Shorts.",
        "================================================================================\n",
        "================================================================================",
        "QUICK 1-CLICK COPY LIST (TITLE + 5 HASHTAGS)",
        "================================================================================\n",
    ]

    for item in clips_summary:
        idx = item["idx"]
        title = item["title"]
        tags_str = " ".join(item["hashtags"])
        filename = item.get("filename", f"clip_{idx:02d}.mp4")

        lines.append(f"VIDEO {idx:02d} ({filename})")
        lines.append("TITLE:")
        lines.append(f"{title}")
        lines.append("HASHTAGS (5):")
        lines.append(f"{tags_str}")
        lines.append("")

    lines.append("\n================================================================================")
    lines.append("DETAILED VIDEO BREAKDOWN (WITH PLATFORM DESCRIPTIONS)")
    lines.append("================================================================================\n")

    for item in clips_summary:
        idx = item["idx"]
        cl: RenderedClip = item["clip"]
        title = item["title"]
        tags_str = " ".join(item["hashtags"])
        filename = item.get("filename", f"clip_{idx:02d}.mp4")
        dur = item.get("duration", cl.duration)

        lines.append("--------------------------------------------------------------------------------")
        lines.append(f"VIDEO {idx:02d} | Duration: {dur:.1f}s | File: {filename}")
        lines.append("--------------------------------------------------------------------------------")
        lines.append("[TITLE]")
        lines.append(f"{title}\n")
        lines.append("[5 HASHTAGS]")
        lines.append(f"{tags_str}\n")
        if cl.tiktok_caption:
            lines.append("[TIKTOK / REELS CAPTION]")
            lines.append(f"{cl.tiktok_caption}\n")
        if cl.shorts_title and cl.shorts_title != title:
            lines.append("[YOUTUBE SHORTS TITLE]")
            lines.append(f"{cl.shorts_title}\n")
        if cl.shorts_description:
            lines.append("[DESCRIPTION]")
            lines.append(f"{cl.shorts_description}\n")
        lines.append("")

    return "\n".join(lines)


def build_title_text_content(cl: RenderedClip, idx: int) -> str:
    """Format a clean, creator-ready title & caption text document for an individual clip."""
    five_tags = extract_5_hashtags(cl)
    five_tags_str = " ".join(five_tags)

    title_main = cl.hook_header_text or cl.tiktok_title or cl.shorts_title or f"Viral Clip {idx:02d}"

    return (
        f"==================================================\n"
        f"CLIP {idx:02d}: {title_main}\n"
        f"==================================================\n\n"
        f"[TITLE]\n"
        f"{title_main}\n\n"
        f"[5 HASHTAGS]\n"
        f"{five_tags_str}\n\n"
        f"[TIKTOK / REELS CAPTION]\n"
        f"{cl.tiktok_caption or cl.reels_caption or ''}\n\n"
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
    2. 'titles_and_thumbnails/' — contains thumbnails, title text files, and
       a consolidated 'all_titles_and_hashtags.txt' with titles & 5 hashtags for each video.
    """
    stmt = select(RenderedClip).where(RenderedClip.job_id == job_id)
    res = await db.execute(stmt)
    clips = res.scalars().all()

    if not clips:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rendered clips found for this job.")

    clips_summary: List[Dict[str, Any]] = []
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, cl in enumerate(clips, start=1):
            title_hint = cl.hook_header_text or cl.tiktok_title or cl.shorts_title or f"clip_{idx:02d}"
            slug = slugify_title(title_hint)
            base_name = f"clip_{idx:02d}_{cl.id[:6]}_{slug}"
            five_tags = extract_5_hashtags(cl)

            clips_summary.append({
                "idx": idx,
                "clip": cl,
                "title": title_hint,
                "hashtags": five_tags,
                "filename": f"{base_name}.mp4",
                "duration": cl.duration,
            })

            # Folder 1: videos/ (ONLY .mp4 files)
            if cl.video_path and Path(cl.video_path).exists():
                zf.write(cl.video_path, arcname=f"videos/{base_name}.mp4")

            # Folder 2: titles_and_thumbnails/ (thumbnails, individual title txt, metadata)
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
                    "hashtags": five_tags,
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

        # Single consolidated text file with all titles & 5 hashtags in titles_and_thumbnails folder
        all_titles_text = build_batch_titles_and_hashtags_text(clips_summary)
        zf.writestr("titles_and_thumbnails/all_titles_and_hashtags.txt", all_titles_text)
        zf.writestr("titles_and_thumbnails/titles_and_hashtags.txt", all_titles_text)

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
    2. 'titles_and_thumbnails/' — contains thumbnails, individual title text files,
       and a consolidated 'all_titles_and_hashtags.txt' with titles & 5 hashtags for each video.
    """
    clip_ids = payload.get("clip_ids", [])
    if not clip_ids:
        raise HTTPException(status_code=400, detail="No clip IDs provided.")

    stmt = select(RenderedClip).where(RenderedClip.id.in_(clip_ids))
    res = await db.execute(stmt)
    clips = res.scalars().all()

    if not clips:
        raise HTTPException(status_code=404, detail="No matching clips found.")

    clips_summary: List[Dict[str, Any]] = []
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, cl in enumerate(clips, start=1):
            title_hint = cl.hook_header_text or cl.tiktok_title or cl.shorts_title or f"clip_{idx:02d}"
            slug = slugify_title(title_hint)
            base_name = f"clip_{idx:02d}_{cl.id[:6]}_{slug}"
            five_tags = extract_5_hashtags(cl)

            clips_summary.append({
                "idx": idx,
                "clip": cl,
                "title": title_hint,
                "hashtags": five_tags,
                "filename": f"{base_name}.mp4",
                "duration": cl.duration,
            })

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
                    "hashtags": five_tags,
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

        # Single consolidated text file with all titles & 5 hashtags in titles_and_thumbnails folder
        all_titles_text = build_batch_titles_and_hashtags_text(clips_summary)
        zf.writestr("titles_and_thumbnails/all_titles_and_hashtags.txt", all_titles_text)
        zf.writestr("titles_and_thumbnails/titles_and_hashtags.txt", all_titles_text)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=selected_clips_{len(clips)}_batch.zip"},
    )


@router.get("/job/{job_id}/titles-and-hashtags")
async def get_job_titles_and_hashtags_text(
    job_id: str,
    download: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single clean text file with titles and 5 hashtags for all videos in a job.
    Can be previewed as plain text or downloaded directly as .txt.
    """
    stmt = select(RenderedClip).where(RenderedClip.job_id == job_id)
    res = await db.execute(stmt)
    clips = res.scalars().all()

    if not clips:
        raise HTTPException(status_code=404, detail="No rendered clips found for this job.")

    clips_summary = []
    for idx, cl in enumerate(clips, start=1):
        title_hint = cl.hook_header_text or cl.tiktok_title or cl.shorts_title or f"clip_{idx:02d}"
        slug = slugify_title(title_hint)
        base_name = f"clip_{idx:02d}_{cl.id[:6]}_{slug}"
        five_tags = extract_5_hashtags(cl)
        clips_summary.append({
            "idx": idx,
            "clip": cl,
            "title": title_hint,
            "hashtags": five_tags,
            "filename": f"{base_name}.mp4",
            "duration": cl.duration,
        })

    text_content = build_batch_titles_and_hashtags_text(clips_summary)

    headers = {}
    if download:
        headers["Content-Disposition"] = f"attachment; filename=job_{job_id[:8]}_titles_and_hashtags.txt"

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=text_content, headers=headers)

