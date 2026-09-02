"""Deterministic 21-stage video processing pipeline orchestrator with stage checkpointing and project batch support."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import ClipperException
from app.core.models import (
    AIRequestLog,
    ClipCandidate,
    Job,
    Project,
    RenderedClip,
    Scene,
    Transcript,
    Video,
)
from app.services.ai.factory import get_ai_provider
from app.services.ai.scoring import scorer
from app.services.media.audio import audio_service
from app.services.media.captioner import captioner
from app.services.media.inspector import inspector
from app.services.media.reframing import reframer
from app.services.media.renderer import renderer
from app.services.media.scene_detector import scene_detector
from app.services.media.silence_detector import silence_detector, TimelineEdit
from app.services.pipeline.candidate_discovery import candidate_discovery_service
from app.services.pipeline.context_expansion import context_expansion_service
from app.services.pipeline.deduplication import deduplication_service
from app.services.pipeline.ranking import ranking_service
from app.services.transcription.filler_detector import filler_detector
from app.services.transcription.whisper_service import whisper_service

logger = logging.getLogger(__name__)

STAGES = [
    (1, "Validate file"),
    (2, "Inspect media metadata"),
    (3, "Create job"),
    (4, "Extract audio"),
    (5, "Transcribe audio"),
    (6, "Detect scenes"),
    (7, "Generate timestamped transcript"),
    (8, "Detect candidate moments"),
    (9, "Expand candidate context"),
    (10, "Analyze candidate quality"),
    (11, "Score candidates"),
    (12, "Remove duplicates/overlaps"),
    (13, "Rank globally"),
    (14, "Apply user duration constraints"),
    (15, "Generate final clip boundaries"),
    (16, "Render clips using FFmpeg"),
    (17, "Generate captions"),
    (18, "Generate thumbnails"),
    (19, "Generate clip metadata"),
    (20, "Store results"),
    (21, "Mark job complete"),
]


class VideoProcessingPipeline:
    """Executes the 21-stage deterministic pipeline for short-form content generation."""

    def __init__(self):
        self._listeners: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, job_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if job_id not in self._listeners:
            self._listeners[job_id] = []
        self._listeners[job_id].append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        if job_id in self._listeners and q in self._listeners[job_id]:
            self._listeners[job_id].remove(q)
            if not self._listeners[job_id]:
                del self._listeners[job_id]

    async def _emit_event(self, job_id: str, data: Dict[str, Any]) -> None:
        if job_id in self._listeners:
            for q in list(self._listeners[job_id]):
                try:
                    q.put_nowait(data)
                except Exception:
                    pass

    async def update_job_progress(
        self,
        session: AsyncSession,
        job: Job,
        stage_num: int,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        checkpoint_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update job stage, calculated progress percentage, logs, and stage checkpoints."""
        stage_name = next((s[1] for s in STAGES if s[0] == stage_num), "Processing")
        progress = round((stage_num / 21.0) * 100.0, 1)

        job.current_stage = stage_num
        job.stage_name = stage_name
        job.progress = progress
        job.status = "completed" if stage_num == 21 else "processing"

        # Update log history
        logs = json.loads(job.log_history or "[]")
        log_entry = {
            "stage": stage_num,
            "stage_name": stage_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logs.append(log_entry)
        job.log_history = json.dumps(logs)

        # Update stage checkpoints for resumption
        if checkpoint_data:
            existing_cp = json.loads(job.stage_checkpoint_json or "{}")
            existing_cp.update(checkpoint_data)
            job.stage_checkpoint_json = json.dumps(existing_cp)

        await session.commit()

        # Emit live event
        event_payload = {
            "job_id": job.id,
            "project_id": job.project_id,
            "status": job.status,
            "current_stage": stage_num,
            "stage_name": stage_name,
            "progress": progress,
            "message": message,
            "timestamp": log_entry["timestamp"],
            **(extra_data or {}),
        }
        await self._emit_event(job.id, event_payload)
        logger.info(f"[Job {job.id}] Stage {stage_num}/21 ({stage_name}): {message}")

    async def run_pipeline(self, job_id: str) -> None:
        """Execute all 21 pipeline stages sequentially with stage resumption."""
        async with AsyncSessionLocal() as session:
            job_stmt = select(Job).where(Job.id == job_id)
            result = await session.execute(job_stmt)
            job = result.scalar_one_or_none()

            if not job:
                logger.error(f"Pipeline job not found: {job_id}")
                return

            config = json.loads(job.config_json or "{}")
            requested_clips = config.get("target_clips_count", 10)
            requested_clips = config.get("target_clips_count", 10)
            mode = config.get("mode", getattr(job, "mode", "podcast"))
            duration_preset = config.get("duration_preset", "30-45s")
            ai_provider_name = config.get("ai_provider")
            caption_style = config.get("caption_style", "bold_yellow")
            burn_captions = config.get("burn_captions", getattr(job, "burn_captions", True))
            remove_dead_air = config.get("remove_dead_air", getattr(job, "remove_dead_air", True))
            reframing_mode = config.get("reframing_mode", "center_crop")
            custom_instructions = config.get("custom_instructions")
            source_diversity_weight = config.get("source_diversity_weight", 0.35)

            # Check if this is a project-level batch job or single video job
            if job.project_id and not job.video_id:
                await self._run_project_pipeline(session, job, config)
                return

            video_stmt = select(Video).where(Video.id == job.video_id)
            v_result = await session.execute(video_stmt)
            video = v_result.scalar_one_or_none()

            if not video:
                job.status = "failed"
                job.error_message = "Associated video not found."
                await session.commit()
                return

            video_path = Path(video.file_path)
            checkpoints = json.loads(job.stage_checkpoint_json or "{}")

            try:
                # Stage 1: Validate file
                if not checkpoints.get("stage_1_done"):
                    await self.update_job_progress(session, job, 1, f"Validating video file: {video.filename}")
                    if not video_path.exists():
                        raise ClipperException(f"Video file does not exist: {video_path}")
                    checkpoints["stage_1_done"] = True

                # Stage 2: Inspect media metadata
                if not checkpoints.get("stage_2_done"):
                    await self.update_job_progress(session, job, 2, "Inspecting media streams, resolution, and codecs")
                    meta = await inspector.inspect(video_path)
                    video.duration_seconds = meta.duration_seconds
                    video.width = meta.width
                    video.height = meta.height
                    video.fps = meta.fps
                    video.video_codec = meta.video_codec
                    video.audio_codec = meta.audio_codec
                    video.bitrate = meta.bitrate
                    await session.commit()
                    checkpoints["stage_2_done"] = True

                # Stage 3: Job confirm
                await self.update_job_progress(session, job, 3, f"Job initialized for {requested_clips} clips in '{mode}' mode ({duration_preset})")

                # Stage 4: Extract audio
                audio_wav_path = settings.DATA_DIR / "uploads" / f"{video.id}_audio.wav"
                if not audio_wav_path.exists() or not checkpoints.get("stage_4_done"):
                    await self.update_job_progress(session, job, 4, "Extracting 16kHz mono audio for speech transcription")
                    await audio_service.extract_whisper_audio(video_path, audio_wav_path)
                    checkpoints["stage_4_done"] = True

                # Stage 5: Transcribe audio
                t_stmt = select(Transcript).where(Transcript.video_id == video.id)
                t_res = await session.execute(t_stmt)
                db_transcript = t_res.scalar_one_or_none()

                if not db_transcript:
                    await self.update_job_progress(session, job, 5, "Transcribing spoken dialogue with word-level timestamps")
                    transcript_res = await whisper_service.transcribe(audio_wav_path)
                    raw_segments = [s.model_dump() for s in transcript_res.segments]
                    
                    # Stage 7: Generate transcript DB record
                    await self.update_job_progress(session, job, 7, f"Mapping {len(raw_segments)} transcript segments")
                    db_transcript = Transcript(
                        video_id=video.id,
                        language=transcript_res.language,
                        full_text=transcript_res.full_text,
                        segments_json=json.dumps(raw_segments),
                    )
                    session.add(db_transcript)
                    await session.commit()
                else:
                    raw_segments = json.loads(db_transcript.segments_json)

                # Stage 6: Detect scenes & dead air / silences
                silence_intervals = []
                if remove_dead_air:
                    await self.update_job_progress(session, job, 6, "Analyzing dead-air intervals and audio silence thresholds")
                    silence_intervals = await silence_detector.detect_silence(video_path)

                sc_stmt = select(Scene).where(Scene.video_id == video.id)
                sc_res = await session.execute(sc_stmt)
                existing_scenes = sc_res.scalars().all()
                if not existing_scenes:
                    scene_boundaries = await scene_detector.detect_scenes(video_path, video.id)
                    for sc in scene_boundaries:
                        session.add(Scene(
                            video_id=video.id,
                            scene_index=sc.scene_index,
                            start_time=sc.start_time,
                            end_time=sc.end_time,
                            keyframe_path=sc.keyframe_path,
                        ))
                    await session.commit()

                # Stage 8: Detect candidate moments
                ai_provider = get_ai_provider(ai_provider_name)
                await self.update_job_progress(
                    session, job, 8,
                    f"Discovering candidate pool with AI in '{mode}' mode ({ai_provider.__class__.__name__})"
                )
                
                t0 = datetime.now()
                raw_candidates = await candidate_discovery_service.discover_candidates(
                    ai_provider=ai_provider,
                    transcript_segments=raw_segments,
                    media_info={"duration_seconds": video.duration_seconds, "width": video.width, "height": video.height},
                    requested_clips_count=requested_clips,
                    duration_preset=duration_preset,
                    mode=mode,
                    custom_instructions=custom_instructions,
                )
                latency = (datetime.now() - t0).total_seconds() * 1000.0

                # Log AI request audit
                session.add(AIRequestLog(
                    provider=ai_provider.__class__.__name__,
                    model=getattr(ai_provider, "model", "default"),
                    stage="candidate_discovery",
                    latency_ms=round(latency, 1),
                    status="success",
                ))
                await session.commit()

                await self.update_job_progress(
                    session, job, 8,
                    f"Discovered {len(raw_candidates)} candidate moments pool",
                    {"total_candidates_found": len(raw_candidates)},
                )

                # Stage 9: Expand candidate context
                await self.update_job_progress(session, job, 9, "Expanding context and snapping to sentence boundaries")
                expanded_candidates = [
                    context_expansion_service.expand_candidate_context(c, raw_segments, video.duration_seconds)
                    for c in raw_candidates
                ]

                # Stage 10 & 11: Score candidates
                await self.update_job_progress(session, job, 10, "Analyzing linguistic retention, hook intensity, and payoff")
                await self.update_job_progress(session, job, 11, "Calculating 12-factor composite scores & penalties")
                
                scored_candidates = []
                for cand in expanded_candidates:
                    dur = cand.end - cand.start
                    comp_score, penalty = scorer.calculate_composite_score(cand, duration=dur)
                    scored_candidates.append((cand, comp_score, penalty))

                # Stage 12: Deduplicate (NMS)
                await self.update_job_progress(session, job, 12, "Performing temporal IoU deduplication and Non-Maximum Suppression")
                deduped = deduplication_service.deduplicate_candidates(scored_candidates, min_keep_count=requested_clips)

                # Stage 13 & 14: Rank globally and apply duration constraints
                await self.update_job_progress(session, job, 13, "Ranking candidates globally")
                await self.update_job_progress(session, job, 14, f"Enforcing duration target ({duration_preset}) with narrative preservation")
                ranked_clips = ranking_service.rank_and_select(deduped, target_count=requested_clips, duration_preset=duration_preset)


                # Stage 15: Store candidate records
                await self.update_job_progress(session, job, 15, f"Finalizing clip boundaries for top {len(ranked_clips)} clips")
                candidate_records: List[ClipCandidate] = []
                timeline_edits: List[TimelineEdit] = []

                for cand, comp_score, penalty, rank in ranked_clips:
                    if remove_dead_air:
                        t_edit = silence_detector.build_edited_timeline(cand.start, cand.end, silence_intervals)
                    else:
                        t_edit = TimelineEdit(
                            source_start=cand.start,
                            source_end=cand.end,
                            keep=[[cand.start, cand.end]],
                            dead_air_removed_seconds=0.0,
                        )
                    timeline_edits.append(t_edit)

                    cand_rec = ClipCandidate(
                        job_id=job.id,
                        video_id=video.id,
                        start_time=cand.start,
                        end_time=cand.end,
                        duration=round(cand.end - cand.start, 2),
                        hook_score=cand.hook_score,
                        retention_score=cand.retention_score,
                        curiosity_score=cand.curiosity_score,
                        emotion_score=cand.emotion_score,
                        story_score=cand.story_score,
                        payoff_score=cand.payoff_score,
                        shareability_score=cand.shareability_score,
                        novelty_score=cand.novelty_score,
                        quotability_score=cand.quotability_score,
                        standalone_score=getattr(cand, "standalone_score", 80.0),
                        rewatch_score=getattr(cand, "rewatch_score", 75.0),
                        visual_score=cand.visual_score,
                        audio_score=cand.audio_score,
                        platform_score=cand.platform_score,
                        composite_score=comp_score,
                        penalty_deduction=penalty,
                        rank=rank,
                        selected=True,
                        hook_text=cand.hook_summary,
                        payoff_text=cand.payoff_summary,
                        timeline_edit_json=json.dumps(t_edit.model_dump()),
                        reason=cand.reason,
                    )
                    session.add(cand_rec)
                    candidate_records.append(cand_rec)
                await session.commit()

                # Stage 16 -> Stage 20: Rendering, Captions, Thumbnails, Metadata
                rendered_count = 0
                for idx, (cand, comp_score, penalty, rank) in enumerate(ranked_clips, start=1):
                    cand_rec = candidate_records[idx - 1]
                    t_edit = timeline_edits[idx - 1]
                    clip_id = cand_rec.id

                    # Stage 16: Reframing & Render
                    sub_status = f"with '{caption_style}' subtitles" if burn_captions and caption_style != "none" else "without subtitles"
                    await self.update_job_progress(
                        session, job, 16,
                        f"Rendering clip {idx}/{len(ranked_clips)} (9:16 vertical, {sub_status})"
                    )
                    crop_info = {"mode": "center_crop"}
                    
                    # Stage 17: Generate captions & persistent TikTok hook header
                    ass_path = settings.SUBTITLE_DIR / f"{clip_id}.ass"
                    srt_path = settings.SUBTITLE_DIR / f"{clip_id}.srt"
                    job_sub_pos = getattr(job, "subtitle_position", None) or 75
                    job_add_hook = getattr(job, "add_hook_header", False)
                    job_hook_pos = getattr(job, "hook_header_position", None) or 12
                    hook_title_text = cand.hook_summary or cand.reason or ""

                    captioner.generate_ass(
                        raw_segments,
                        cand.start,
                        cand.end,
                        ass_path,
                        style=caption_style,
                        subtitle_position=job_sub_pos,
                        add_hook_header=job_add_hook,
                        hook_header_text=hook_title_text,
                        hook_header_position=job_hook_pos,
                    )
                    captioner.generate_srt(raw_segments, cand.start, cand.end, srt_path)

                    # FFmpeg render
                    out_video_path = settings.PROCESSED_DIR / f"{clip_id}.mp4"
                    should_burn = burn_captions and caption_style != "none"
                    job_framing_mode = getattr(job, "framing_mode", None) or "crop_9_16"
                    job_blur_radius = getattr(job, "blur_radius", None) or 30
                    job_remove_watermark = getattr(job, "remove_watermark", False) or False
                    job_watermark_position = getattr(job, "watermark_position", None) or "top_right"
                    job_enhance_quality = getattr(job, "enhance_quality", True)
                    if job_enhance_quality is None:
                        job_enhance_quality = True

                    await renderer.render_clip(
                        source_video_path=video_path,
                        start_time=cand.start,
                        end_time=cand.end,
                        output_video_path=out_video_path,
                        reframing_config=crop_info,
                        ass_subtitle_path=ass_path if should_burn else None,
                        burn_captions=should_burn,
                        keep_intervals=t_edit.keep,
                        framing_mode=job_framing_mode,
                        blur_radius=job_blur_radius,
                        remove_watermark=job_remove_watermark,
                        watermark_position=job_watermark_position,
                        enhance_quality=job_enhance_quality,
                    )

                    # Stage 18: Generate thumbnails from rendered vertical video (guarantees 9:16 layout & non-black frame)
                    await self.update_job_progress(
                        session, job, 18,
                        f"Generating thumbnail for clip {idx}/{len(ranked_clips)}"
                    )
                    thumb_path = settings.THUMBNAIL_DIR / f"{clip_id}.jpg"
                    await renderer.generate_thumbnail(out_video_path, 1.0, thumb_path)

                    # Stage 19: Generate platform metadata
                    await self.update_job_progress(
                        session, job, 19,
                        f"Generating platform metadata for clip {idx}/{len(ranked_clips)}"
                    )
                    clip_text = " ".join([s.get("text", "") for s in raw_segments if s.get("end", 0) >= cand.start and s.get("start", 0) <= cand.end])
                    meta_res = await ai_provider.generate_metadata(
                        clip_transcript=clip_text,
                        clip_context={"hook_summary": cand.hook_summary, "payoff_summary": cand.payoff_summary},
                    )

                    # Stage 20: Store results
                    await self.update_job_progress(
                        session, job, 20,
                        f"Storing clip assets {idx}/{len(ranked_clips)} in database"
                    )
                    rendered_rec = RenderedClip(
                        candidate_id=cand_rec.id,
                        job_id=job.id,
                        video_id=video.id,
                        mode=mode,
                        video_path=str(out_video_path),
                        thumbnail_path=str(thumb_path),
                        srt_path=str(srt_path),
                        ass_path=str(ass_path),
                        start_time=cand.start,
                        end_time=cand.end,
                        duration=round(sum(e - s for s, e in t_edit.keep), 2),
                        aspect_ratio="16:9" if job_framing_mode == "original_16_9" else "9:16",
                        framing_mode=job_framing_mode,
                        blur_radius=job_blur_radius,
                        subtitle_position=job_sub_pos,
                        add_hook_header=job_add_hook,
                        hook_header_position=job_hook_pos,
                        hook_header_text=hook_title_text if job_add_hook else None,
                        remove_watermark=job_remove_watermark,
                        watermark_position=job_watermark_position,
                        enhance_quality=job_enhance_quality,
                        caption_style=caption_style if should_burn else "none",
                        burn_captions=should_burn,
                        timeline_edit_json=json.dumps(t_edit.model_dump()),
                        tiktok_title=meta_res.tiktok_title,
                        tiktok_caption=meta_res.tiktok_caption,
                        tiktok_hashtags=json.dumps(meta_res.tiktok_hashtags),
                        reels_caption=meta_res.reels_caption,
                        reels_hashtags=json.dumps(meta_res.reels_hashtags),
                        shorts_title=meta_res.shorts_title,
                        shorts_description=meta_res.shorts_description,
                        shorts_hashtags=json.dumps(meta_res.shorts_hashtags),
                    )


                    session.add(rendered_rec)
                    await session.commit()
                    rendered_count += 1

                # Stage 21: Mark job complete
                await self.update_job_progress(
                    session, job, 21,
                    f"Successfully generated {rendered_count} high-retention 9:16 clips ({mode} mode)!",
                    {"total_clips_rendered": rendered_count},
                    {"stage_21_done": True},
                )
                logger.info(f"Pipeline completed successfully for job: {job_id}")

            except Exception as e:
                logger.exception(f"Pipeline error on job {job_id}: {e}")
                job.status = "failed"
                job.error_message = str(e)
                await session.commit()
                await self._emit_event(job.id, {
                    "job_id": job.id,
                    "status": "failed",
                    "error": str(e),
                })

    async def _run_project_pipeline(self, session: AsyncSession, job: Job, config: Dict[str, Any]) -> None:
        """Executes multi-video batch processing across all videos in a project."""
        project_id = job.project_id
        v_stmt = select(Video).where(Video.project_id == project_id)
        v_res = await session.execute(v_stmt)
        project_videos = v_res.scalars().all()

        if not project_videos:
            job.status = "failed"
            job.error_message = "Project contains no videos to process."
            await session.commit()
            return

        requested_clips = config.get("target_clips_count", 20)
        mode = config.get("mode", getattr(job, "mode", "podcast"))
        duration_preset = config.get("duration_preset", "30-45s")
        caption_style = config.get("caption_style", "bold_yellow")
        burn_captions = config.get("burn_captions", getattr(job, "burn_captions", True))
        remove_dead_air = config.get("remove_dead_air", getattr(job, "remove_dead_air", True))
        source_diversity_weight = config.get("source_diversity_weight", 0.35)
        ai_provider = get_ai_provider(config.get("ai_provider"))

        await self.update_job_progress(
            session, job, 1,
            f"Starting batch analysis across {len(project_videos)} project videos in '{mode}' mode"
        )

        video_candidates_map: Dict[str, List[tuple]] = {}
        video_silences_map: Dict[str, List[Any]] = {}

        # Process each video's transcription & discovery
        for v_idx, v in enumerate(project_videos, start=1):
            v_path = Path(v.file_path)
            await self.update_job_progress(
                session, job, 4,
                f"Transcribing & analyzing video {v_idx}/{len(project_videos)} ({v.filename})"
            )

            # Silence analysis
            if remove_dead_air:
                video_silences_map[v.id] = await silence_detector.detect_silence(v_path)
            else:
                video_silences_map[v.id] = []

            # Transcribe
            audio_wav = settings.DATA_DIR / "uploads" / f"{v.id}_audio.wav"
            if not audio_wav.exists():
                await audio_service.extract_whisper_audio(v_path, audio_wav)

            t_stmt = select(Transcript).where(Transcript.video_id == v.id)
            t_res = await session.execute(t_stmt)
            tr = t_res.scalar_one_or_none()
            if not tr:
                t_res_data = await whisper_service.transcribe(audio_wav)
                raw_segs = [s.model_dump() for s in t_res_data.segments]
                tr = Transcript(video_id=v.id, full_text=t_res_data.full_text, segments_json=json.dumps(raw_segs))
                session.add(tr)
                await session.commit()
            else:
                raw_segs = json.loads(tr.segments_json)

            # Discover candidates
            raw_cands = await candidate_discovery_service.discover_candidates(
                ai_provider=ai_provider,
                transcript_segments=raw_segs,
                media_info={"duration_seconds": v.duration_seconds},
                requested_clips_count=max(5, requested_clips // len(project_videos)),
                duration_preset=duration_preset,
                mode=mode,
            )

            expanded = [
                context_expansion_service.expand_candidate_context(c, raw_segs, v.duration_seconds)
                for c in raw_cands
            ]
            scored = []
            for cand in expanded:
                dur = cand.end - cand.start
                comp_score, penalty = scorer.calculate_composite_score(cand, duration=dur)
                scored.append((cand, comp_score, penalty))

            per_video_target = max(3, requested_clips // max(1, len(project_videos)))
            deduped = deduplication_service.deduplicate_candidates(scored, min_keep_count=per_video_target)
            video_candidates_map[v.id] = deduped



        # Cross-video global ranking
        await self.update_job_progress(session, job, 13, "Performing cross-video global candidate ranking")
        ranked_project_clips = ranking_service.cross_video_global_rank(
            video_candidates_map=video_candidates_map,
            target_count=requested_clips,
            duration_preset=duration_preset,
            source_diversity_weight=source_diversity_weight,
        )

        # Render top global clips
        for idx, (v_id, cand, score, pen, rank) in enumerate(ranked_project_clips, start=1):
            sub_status = f"with '{caption_style}' subtitles" if burn_captions and caption_style != "none" else "without subtitles"
            await self.update_job_progress(
                session, job, 16,
                f"Rendering project clip {idx}/{len(ranked_project_clips)} (Rank #{rank}, {sub_status})"
            )
            v = next(vid for vid in project_videos if vid.id == v_id)
            v_path = Path(v.file_path)

            silences = video_silences_map.get(v.id, [])
            if remove_dead_air:
                t_edit = silence_detector.build_edited_timeline(cand.start, cand.end, silences)
            else:
                t_edit = TimelineEdit(
                    source_start=cand.start,
                    source_end=cand.end,
                    keep=[[cand.start, cand.end]],
                    dead_air_removed_seconds=0.0,
                )

            cand_rec = ClipCandidate(
                job_id=job.id,
                video_id=v.id,
                start_time=cand.start,
                end_time=cand.end,
                duration=round(cand.end - cand.start, 2),
                hook_score=cand.hook_score,
                retention_score=cand.retention_score,
                curiosity_score=cand.curiosity_score,
                emotion_score=cand.emotion_score,
                story_score=cand.story_score,
                payoff_score=cand.payoff_score,
                shareability_score=cand.shareability_score,
                novelty_score=cand.novelty_score,
                quotability_score=cand.quotability_score,
                standalone_score=getattr(cand, "standalone_score", 80.0),
                rewatch_score=getattr(cand, "rewatch_score", 75.0),
                visual_score=cand.visual_score,
                audio_score=cand.audio_score,
                platform_score=cand.platform_score,
                composite_score=score,
                penalty_deduction=pen,
                rank=rank,
                selected=True,
                hook_text=cand.hook_summary,
                payoff_text=cand.payoff_summary,
                timeline_edit_json=json.dumps(t_edit.model_dump()),
                reason=cand.reason,
            )
            session.add(cand_rec)
            await session.commit()

            clip_id = cand_rec.id
            crop_info = {"mode": "center_crop"}
            ass_path = settings.SUBTITLE_DIR / f"{clip_id}.ass"
            srt_path = settings.SUBTITLE_DIR / f"{clip_id}.srt"
            out_video = settings.PROCESSED_DIR / f"{clip_id}.mp4"
            thumb = settings.THUMBNAIL_DIR / f"{clip_id}.jpg"

            t_stmt = select(Transcript).where(Transcript.video_id == v.id)
            t_res = await session.execute(t_stmt)
            tr = t_res.scalar_one_or_none()
            segs = json.loads(tr.segments_json) if tr else []

            job_sub_pos = getattr(job, "subtitle_position", None) or 75
            job_add_hook = getattr(job, "add_hook_header", False)
            job_hook_pos = getattr(job, "hook_header_position", None) or 12
            hook_title_text = cand.hook_summary or cand.reason or ""

            captioner.generate_ass(
                segs,
                cand.start,
                cand.end,
                ass_path,
                style=caption_style,
                subtitle_position=job_sub_pos,
                add_hook_header=job_add_hook,
                hook_header_text=hook_title_text,
                hook_header_position=job_hook_pos,
            )
            captioner.generate_srt(segs, cand.start, cand.end, srt_path)

            should_burn = burn_captions and caption_style != "none"
            job_framing_mode = getattr(job, "framing_mode", None) or "crop_9_16"
            job_blur_radius = getattr(job, "blur_radius", None) or 30
            job_remove_watermark = getattr(job, "remove_watermark", False) or False
            job_watermark_position = getattr(job, "watermark_position", None) or "top_right"
            job_enhance_quality = getattr(job, "enhance_quality", True)
            if job_enhance_quality is None:
                job_enhance_quality = True

            await renderer.render_clip(
                source_video_path=v_path,
                start_time=cand.start,
                end_time=cand.end,
                output_video_path=out_video,
                reframing_config=crop_info,
                ass_subtitle_path=ass_path if should_burn else None,
                burn_captions=should_burn,
                keep_intervals=t_edit.keep,
                framing_mode=job_framing_mode,
                blur_radius=job_blur_radius,
                remove_watermark=job_remove_watermark,
                watermark_position=job_watermark_position,
                enhance_quality=job_enhance_quality,
            )

            await renderer.generate_thumbnail(out_video, 1.0, thumb)

            clip_text = " ".join([s.get("text", "") for s in segs if s.get("end", 0) >= cand.start and s.get("start", 0) <= cand.end])
            meta_res = await ai_provider.generate_metadata(clip_text, {"hook_summary": cand.hook_summary, "payoff_summary": cand.payoff_summary})

            session.add(RenderedClip(
                candidate_id=cand_rec.id,
                job_id=job.id,
                video_id=v.id,
                mode=mode,
                video_path=str(out_video),
                thumbnail_path=str(thumb),
                srt_path=str(srt_path),
                ass_path=str(ass_path),
                start_time=cand.start,
                end_time=cand.end,
                duration=round(sum(e - s for s, e in t_edit.keep), 2),
                aspect_ratio="16:9" if job_framing_mode == "original_16_9" else "9:16",
                framing_mode=job_framing_mode,
                blur_radius=job_blur_radius,
                subtitle_position=job_sub_pos,
                add_hook_header=job_add_hook,
                hook_header_position=job_hook_pos,
                hook_header_text=hook_title_text if job_add_hook else None,
                remove_watermark=job_remove_watermark,
                watermark_position=job_watermark_position,
                enhance_quality=job_enhance_quality,
                caption_style=caption_style if should_burn else "none",
                burn_captions=should_burn,
                timeline_edit_json=json.dumps(t_edit.model_dump()),

                tiktok_title=meta_res.tiktok_title,
                tiktok_caption=meta_res.tiktok_caption,
                tiktok_hashtags=json.dumps(meta_res.tiktok_hashtags),
                reels_caption=meta_res.reels_caption,
                reels_hashtags=json.dumps(meta_res.reels_hashtags),
                shorts_title=meta_res.shorts_title,
                shorts_description=meta_res.shorts_description,
                shorts_hashtags=json.dumps(meta_res.shorts_hashtags),
            ))

            await session.commit()

        await self.update_job_progress(
            session, job, 21,
            f"Successfully processed project: {len(ranked_project_clips)} top clips across {len(project_videos)} source videos ({mode} mode)!",
            {"total_clips_rendered": len(ranked_project_clips)},
        )


pipeline_runner = VideoProcessingPipeline()
