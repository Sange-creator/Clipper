"""End-to-end test of the full 21-stage deterministic video processing pipeline."""

import asyncio
import json
import shutil
import pytest
from pathlib import Path
from sqlalchemy import select

from app.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.models import Job, RenderedClip, Video
from app.services.pipeline.pipeline import pipeline_runner
from app.utils.hashing import compute_file_hash


@pytest.mark.asyncio
async def test_end_to_end_21_stage_pipeline(tmp_path):
    await init_db()

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        pytest.skip("FFmpeg is not installed on system.")

    # Create a 6-second synthetic test video with audio using FFmpeg
    test_video_path = tmp_path / "test_source.mp4"
    gen_cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=6:size=640x360:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(test_video_path)
    ]
    proc = await asyncio.create_subprocess_exec(*gen_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.communicate()
    assert test_video_path.exists()

    content_hash = compute_file_hash(test_video_path)

    # Insert test video and job in DB
    async with AsyncSessionLocal() as session:
        v = Video(
            content_hash=content_hash,
            filename="test_source.mp4",
            file_path=str(test_video_path),
            duration_seconds=6.0,
            width=640,
            height=360,
            fps=30.0,
            video_codec="h264",
            audio_codec="aac",
            bitrate=500000,
            file_size_bytes=test_video_path.stat().st_size,
        )
        session.add(v)
        await session.commit()
        await session.refresh(v)

        j = Job(
            video_id=v.id,
            status="queued",
            current_stage=1,
            stage_name="Validate file",
            progress=0.0,
            config_json=json.dumps({
                "target_clips_count": 1,
                "duration_preset": "15-30s",
                "ai_provider": "mock",
                "caption_style": "karaoke_yellow",
                "reframing_mode": "center_crop"
            }),
            log_history=json.dumps([]),
        )
        session.add(j)
        await session.commit()
        await session.refresh(j)
        job_id = j.id

    # Execute all 21 stages
    await pipeline_runner.run_pipeline(job_id)

    # Verify results
    async with AsyncSessionLocal() as session:
        j_stmt = select(Job).where(Job.id == job_id)
        j_res = await session.execute(j_stmt)
        completed_job = j_res.scalar_one()

        assert completed_job.status == "completed"
        assert completed_job.current_stage == 21
        assert completed_job.progress == 100.0

        c_stmt = select(RenderedClip).where(RenderedClip.job_id == job_id)
        c_res = await session.execute(c_stmt)
        clips = c_res.scalars().all()

        assert len(clips) >= 1
        first_clip = clips[0]
        assert Path(first_clip.video_path).exists()
        assert Path(first_clip.thumbnail_path).exists()
        assert Path(first_clip.ass_path).exists()
        assert Path(first_clip.srt_path).exists()
        assert first_clip.aspect_ratio == "9:16"
        assert first_clip.tiktok_title is not None
