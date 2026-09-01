"""Media file streaming endpoint with HTTP Range request support for smooth video seeking."""

import os
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from app.config import settings

router = APIRouter(prefix="/api/media", tags=["Media"])


@router.get("/{file_path:path}")
async def stream_media_file(
    file_path: str,
    request: Request,
    range: str | None = Header(None),
):
    """
    Streams media files (MP4, JPG, ASS, SRT) from storage.
    Supports HTTP 206 Partial Content for instant video player scrubbing.
    """
    full_path = (settings.DATA_DIR / file_path).resolve()

    # Prevent directory traversal outside data dir
    if not str(full_path).startswith(str(settings.DATA_DIR.resolve())):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found.")

    file_size = full_path.stat().st_size
    content_type = "application/octet-stream"
    ext = full_path.suffix.lower()

    if ext == ".mp4":
        content_type = "video/mp4"
    elif ext in (".jpg", ".jpeg"):
        content_type = "image/jpeg"
    elif ext == ".png":
        content_type = "image/png"
    elif ext == ".srt":
        content_type = "text/plain; charset=utf-8"
    elif ext == ".ass":
        content_type = "text/plain; charset=utf-8"

    if not range:
        return FileResponse(
            str(full_path),
            media_type=content_type,
            headers={"Accept-Ranges": "bytes"},
        )

    # Parse Range Header (e.g. bytes=0-1048576)
    try:
        range_val = range.replace("bytes=", "").strip()
        parts = range_val.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
    except ValueError:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid range.")

    if start >= file_size or end >= file_size or start > end:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Range out of bounds.")

    chunk_size = (end - start) + 1

    def iter_file():
        with open(full_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_size
            while bytes_left > 0:
                read_size = min(65536, bytes_left)
                data = f.read(read_size)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": content_type,
    }

    return StreamingResponse(
        iter_file(),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        headers=headers,
    )
