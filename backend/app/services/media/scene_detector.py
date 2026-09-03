"""Scene detection and keyframe extraction using PySceneDetect / OpenCV."""

import asyncio
import logging
from pathlib import Path
import time
from typing import List
import cv2
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class SceneBoundary(BaseModel):
    """Detected scene segment."""
    scene_index: int
    start_time: float
    end_time: float
    keyframe_path: str = ""


class SceneDetectorService:
    """Detects scene cut points and extracts representative keyframes."""

    async def detect_scenes(self, video_path: Path | str, video_id: str, threshold: float = 27.0) -> List[SceneBoundary]:
        """Detect scene boundaries asynchronously with a strict timeout so it never hangs."""
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._sync_detect_scenes,
                    str(video_path),
                    video_id,
                    threshold,
                ),
                timeout=15.0,  # Max 15 seconds! Never hang the pipeline
            )
        except asyncio.TimeoutError:
            logger.warning(f"Scene detection timed out for {video_id}. Falling back to uniform scene segmentation.")
            return self._fallback_scenes(str(video_path), video_id)
        except Exception as e:
            logger.error(f"Scene detection error for {video_id}: {e}")
            return self._fallback_scenes(str(video_path), video_id)

    def _fallback_scenes(self, video_path: str, video_id: str) -> List[SceneBoundary]:
        """Fast fallback generating uniform scenes without heavy decoding."""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 and total_frames > 0 else 60.0
            cap.release()
        except Exception:
            duration = 60.0

        # Partition into ~30s scenes (up to 30 scenes max)
        num_scenes = max(1, min(30, int(duration / 30.0)))
        step = duration / num_scenes
        return [
            SceneBoundary(
                scene_index=i,
                start_time=round(i * step, 2),
                end_time=round(min(duration, (i + 1) * step), 2),
                keyframe_path="",
            )
            for i in range(num_scenes)
        ]

    def _sync_detect_scenes(self, video_path: str, video_id: str, threshold: float) -> List[SceneBoundary]:
        """Synchronous frame-difference scene detection with fast sampling and timeout protection."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Could not open video for scene detection: {video_path}")
            return [SceneBoundary(scene_index=0, start_time=0.0, end_time=30.0)]

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 60.0

        # For long videos (> 120s), do not decode every frame sequentially.
        # Long videos: generate clean 20-30s scene partitions immediately.
        if duration > 120.0 or total_frames > 3600:
            cap.release()
            return self._fast_long_video_scenes(video_path, video_id, duration)

        scenes: List[SceneBoundary] = []
        keyframe_dir = settings.THUMBNAIL_DIR / video_id
        keyframe_dir.mkdir(parents=True, exist_ok=True)

        prev_gray = None
        scene_start_frame = 0
        scene_index = 0
        frame_idx = 0
        sample_step = max(5, int(fps / 2))  # Sample every 0.5s for fast diffing
        t_start = time.time()

        while cap.isOpened():
            # Hard wall-clock limit: 8 seconds max
            if time.time() - t_start > 8.0:
                logger.info("Scene detection reached 8s limit, finalizing scenes.")
                break

            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_step == 0:
                small = cv2.resize(frame, (160, 90))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                if prev_gray is not None:
                    diff = cv2.absdiff(gray, prev_gray)
                    mean_diff = float(diff.mean())

                    frame_delta = frame_idx - scene_start_frame
                    if (mean_diff > threshold and frame_delta >= int(fps * 2.0)) or (frame_delta >= int(fps * 20.0)):
                        start_time = round(scene_start_frame / fps, 2)
                        end_time = round(frame_idx / fps, 2)

                        # Save downscaled keyframe (instant save, no 4K bloat)
                        keyframe_name = f"scene_{scene_index}_{int(start_time)}s.jpg"
                        keyframe_path = keyframe_dir / keyframe_name
                        small_thumb = cv2.resize(frame, (640, 360))
                        cv2.imwrite(str(keyframe_path), small_thumb)

                        scenes.append(SceneBoundary(
                            scene_index=scene_index,
                            start_time=start_time,
                            end_time=end_time,
                            keyframe_path=str(keyframe_path)
                        ))
                        scene_index += 1
                        scene_start_frame = frame_idx
                        if scene_index >= 50:
                            break

                prev_gray = gray

            frame_idx += 1

        if scene_start_frame < total_frames and scene_index < 50:
            start_time = round(scene_start_frame / fps, 2)
            end_time = round(duration, 2)
            scenes.append(SceneBoundary(
                scene_index=scene_index,
                start_time=start_time,
                end_time=end_time,
                keyframe_path="",
            ))

        cap.release()
        return scenes if scenes else [SceneBoundary(scene_index=0, start_time=0.0, end_time=round(duration, 2))]

    def _fast_long_video_scenes(self, video_path: str, video_id: str, duration: float) -> List[SceneBoundary]:
        """Fast scene partition for long-form videos (>2 mins), completing in < 0.05 second."""
        keyframe_dir = settings.THUMBNAIL_DIR / video_id
        keyframe_dir.mkdir(parents=True, exist_ok=True)

        num_scenes = max(1, min(40, int(duration / 30.0)))
        step = duration / num_scenes
        scenes: List[SceneBoundary] = []

        for i in range(num_scenes):
            s_start = round(i * step, 2)
            s_end = round(min(duration, (i + 1) * step), 2)
            scenes.append(SceneBoundary(
                scene_index=i,
                start_time=s_start,
                end_time=s_end,
                keyframe_path="",
            ))

        return scenes


scene_detector = SceneDetectorService()
