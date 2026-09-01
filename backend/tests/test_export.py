"""Tests for single MP4 download, clip ZIP packages, and batch exports."""

import io
import json
import uuid
import zipfile
import pytest

from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.models import Project, Video, Job, ClipCandidate, RenderedClip


@pytest.mark.asyncio
async def test_single_mp4_and_batch_export_endpoints(tmp_path):
    # Setup dummy video file
    dummy_video = tmp_path / "test_clip.mp4"
    dummy_video.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")

    dummy_thumb = tmp_path / "test_thumb.jpg"
    dummy_thumb.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF")

    dummy_srt = tmp_path / "test_captions.srt"
    dummy_srt.write_text("1\n00:00:00,000 --> 00:00:05,000\nHello World\n", encoding="utf-8")

    clip_id_1 = f"clip-{uuid.uuid4().hex}"
    clip_id_2 = f"clip-{uuid.uuid4().hex}"


    async with AsyncSessionLocal() as session:
        proj = Project(name="Export Test Project")
        session.add(proj)
        await session.flush()

        vid = Video(
            project_id=proj.id,
            content_hash="test_content_hash_123",
            filename="test.mp4",
            file_path=str(dummy_video),
            duration_seconds=60.0,
        )
        session.add(vid)
        await session.flush()

        jb = Job(video_id=vid.id, status="completed", current_stage=21)
        session.add(jb)
        await session.flush()

        cand1 = ClipCandidate(
            job_id=jb.id,
            video_id=vid.id,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            composite_score=92.0,
            rank=1,
            selected=True,
        )
        cand2 = ClipCandidate(
            job_id=jb.id,
            video_id=vid.id,
            start_time=30.0,
            end_time=60.0,
            duration=30.0,
            composite_score=88.0,
            rank=2,
            selected=True,
        )
        session.add_all([cand1, cand2])
        await session.flush()

        c1 = RenderedClip(
            id=clip_id_1,
            candidate_id=cand1.id,
            job_id=jb.id,
            video_id=vid.id,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            video_path=str(dummy_video),
            thumbnail_path=str(dummy_thumb),
            srt_path=str(dummy_srt),
            tiktok_title="Clip 1 Viral Title",
            tiktok_hashtags=json.dumps(["#viral", "#fyp"]),
        )
        c2 = RenderedClip(
            id=clip_id_2,
            candidate_id=cand2.id,
            job_id=jb.id,
            video_id=vid.id,
            start_time=30.0,
            end_time=60.0,
            duration=30.0,
            video_path=str(dummy_video),
            thumbnail_path=str(dummy_thumb),
            srt_path=str(dummy_srt),
            tiktok_title="Clip 2 Viral Title",
            tiktok_hashtags=json.dumps(["#trending", "#fyp"]),
        )
        session.add_all([c1, c2])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test 1: Direct single MP4 download
        resp_mp4 = await ac.get(f"/api/export/clip/{clip_id_1}/mp4")
        assert resp_mp4.status_code == 200
        assert "video/mp4" in resp_mp4.headers["content-type"]
        assert len(resp_mp4.content) > 0

        # Test 2: Single clip ZIP package
        resp_zip = await ac.get(f"/api/export/clip/{clip_id_1}")
        assert resp_zip.status_code == 200
        assert "application/zip" in resp_zip.headers["content-type"]
        with zipfile.ZipFile(io.BytesIO(resp_zip.content), "r") as zf:
            namelist = zf.namelist()
            assert f"clip_{clip_id_1[:8]}.mp4" in namelist
            assert "metadata.json" in namelist

        # Test 3: Custom selected clips bulk ZIP
        resp_batch = await ac.post("/api/export/clips/batch", json={"clip_ids": [clip_id_1, clip_id_2]})
        assert resp_batch.status_code == 200
        assert "application/zip" in resp_batch.headers["content-type"]
        with zipfile.ZipFile(io.BytesIO(resp_batch.content), "r") as zf:
            namelist = zf.namelist()
            assert any(clip_id_1[:6] in name for name in namelist)
            assert any(clip_id_2[:6] in name for name in namelist)
