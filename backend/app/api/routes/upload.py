"""Video upload and validation endpoint."""

import logging
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.models import Video
from app.core.schemas import VideoInfo, VideoUploadResponse
from app.services.media.inspector import inspector
from app.utils.hashing import compute_file_hash
from app.utils.storage import get_media_url, sanitize_filename

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["Upload"])


@router.get("/recent", response_model=List[VideoInfo])
async def get_recent_videos(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve recently uploaded videos from library."""
    result = await db.execute(
        select(Video).order_by(Video.created_at.desc()).limit(limit)
    )
    videos = result.scalars().all()
    return [
        VideoInfo(
            id=v.id,
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


@router.post("", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a long-form video file:
    - Validates extension and file integrity.
    - Streams to disk safely.
    - Computes content hash for caching.
    - Extracts media metadata via ffprobe.
    """
    clean_name = sanitize_filename(file.filename or "video.mp4")
    ext = Path(clean_name).suffix.lower()

    if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Save temporary upload to disk
    temp_target = settings.UPLOAD_DIR / f"upload_{clean_name}"
    try:
        with open(temp_target, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"File upload write failed: {e}")
        if temp_target.exists():
            temp_target.unlink()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to write upload to disk.")

    # Compute content hash
    content_hash = compute_file_hash(temp_target)

    # Rename file to hash-based path for deduplication
    final_path = settings.UPLOAD_DIR / f"{content_hash[:16]}_{clean_name}"
    if not final_path.exists():
        temp_target.rename(final_path)
    else:
        temp_target.unlink()

    # Check if previously registered in DB
    stmt = select(Video).where(Video.content_hash == content_hash)
    result = await db.execute(stmt)
    existing_video = result.scalar_one_or_none()

    if existing_video:
        logger.info(f"Reusing existing video record for hash: {content_hash}")
        video_info = VideoInfo(
            id=existing_video.id,
            filename=existing_video.filename,
            duration_seconds=existing_video.duration_seconds,
            width=existing_video.width,
            height=existing_video.height,
            fps=existing_video.fps,
            video_codec=existing_video.video_codec,
            audio_codec=existing_video.audio_codec,
            file_size_bytes=existing_video.file_size_bytes,
            created_at=existing_video.created_at,
            video_url=get_media_url(existing_video.file_path),
        )
        return VideoUploadResponse(
            video=video_info,
            is_duplicate=True,
            message="Video recognized from previous upload. Reusing cached analysis."
        )

    # Inspect media via ffprobe
    try:
        meta = await inspector.inspect(final_path)
    except Exception as e:
        if final_path.exists():
            final_path.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Create video record
    db_video = Video(
        content_hash=content_hash,
        filename=clean_name,
        file_path=str(final_path),
        duration_seconds=meta.duration_seconds,
        width=meta.width,
        height=meta.height,
        fps=meta.fps,
        video_codec=meta.video_codec,
        audio_codec=meta.audio_codec,
        bitrate=meta.bitrate,
        file_size_bytes=meta.file_size_bytes,
    )
    db.add(db_video)
    await db.commit()
    await db.refresh(db_video)

    video_info = VideoInfo(
        id=db_video.id,
        filename=db_video.filename,
        duration_seconds=db_video.duration_seconds,
        width=db_video.width,
        height=db_video.height,
        fps=db_video.fps,
        video_codec=db_video.video_codec,
        audio_codec=db_video.audio_codec,
        file_size_bytes=db_video.file_size_bytes,
        created_at=db_video.created_at,
        video_url=get_media_url(db_video.file_path),
    )

    return VideoUploadResponse(
        video=video_info,
        is_duplicate=False,
        message="Video uploaded and technical metadata inspected successfully."
    )
