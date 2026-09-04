"""Tests for single MP4 download, clip ZIP packages, and batch exports."""

import io
import json
import uuid
import zipfile
import pytest

from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal, init_db
from app.core.models import Project, Video, Job, ClipCandidate, RenderedClip


@pytest.mark.asyncio
async def test_single_mp4_and_batch_export_endpoints(tmp_path):
    await init_db()
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

            # Strict two-folder validation: Only "videos" and "titles_and_thumbnails" allowed
            top_level_folders = {name.split("/")[0] for name in namelist if "/" in name}
            assert top_level_folders == {"videos", "titles_and_thumbnails"}

            # videos/ contains only .mp4 files
            videos = [name for name in namelist if name.startswith("videos/")]
            assert len(videos) == 2
            assert all(v.endswith(".mp4") for v in videos)

            # titles_and_thumbnails/ contains thumbnails, individual title/meta files, and all_titles_and_hashtags.txt
            thumbs_and_titles = [name for name in namelist if name.startswith("titles_and_thumbnails/")]
            assert all(m.endswith((".jpg", ".txt", ".json")) for m in thumbs_and_titles)
            assert any(m.endswith("_title.txt") for m in thumbs_and_titles)
            assert any(m.endswith("_thumbnail.jpg") for m in thumbs_and_titles)
            assert "titles_and_thumbnails/all_titles_and_hashtags.txt" in namelist
            assert "titles_and_thumbnails/titles_and_hashtags.txt" in namelist

            # Validate content of all_titles_and_hashtags.txt
            all_txt = zf.read("titles_and_thumbnails/all_titles_and_hashtags.txt").decode("utf-8")
            assert "ALL TITLES & 5 HASHTAGS" in all_txt
            assert "VIDEO 01" in all_txt
            assert "VIDEO 02" in all_txt
            assert "HASHTAGS (5):" in all_txt

            # Zero root files
            assert all("/" in name for name in namelist)

        # Test 4: Job-level batch export has identical strict two-folder structure & single text file
        resp_job_batch = await ac.get(f"/api/export/job/{jb.id}/batch")
        assert resp_job_batch.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp_job_batch.content), "r") as zf:
            namelist = zf.namelist()
            top_level = {name.split("/")[0] for name in namelist if "/" in name}
            assert top_level == {"videos", "titles_and_thumbnails"}
            assert "titles_and_thumbnails/all_titles_and_hashtags.txt" in namelist
            assert all("/" in name for name in namelist)

        # Test 5: Direct titles-and-hashtags text endpoint
        resp_txt = await ac.get(f"/api/export/job/{jb.id}/titles-and-hashtags")
        assert resp_txt.status_code == 200
        assert "ALL TITLES & 5 HASHTAGS" in resp_txt.text
        assert "VIDEO 01" in resp_txt.text

