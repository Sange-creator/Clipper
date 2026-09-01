"""Scene detection and keyframe extraction using PySceneDetect / OpenCV."""

import asyncio
import logging
from pathlib import Path
from typing import List, Tuple
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
        """Detect scene boundaries asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._sync_detect_scenes,
            str(video_path),
            video_id,
            threshold
        )

    def _sync_detect_scenes(self, video_path: str, video_id: str, threshold: float) -> List[SceneBoundary]:
        """Synchronous frame-difference scene detection and keyframe extraction."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Could not open video for scene detection: {video_path}")
            return [SceneBoundary(scene_index=0, start_time=0.0, end_time=30.0)]

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 60.0

        scenes: List[SceneBoundary] = []
        keyframe_dir = settings.THUMBNAIL_DIR / video_id
        keyframe_dir.mkdir(parents=True, exist_ok=True)

        prev_gray = None
        scene_start_frame = 0
        scene_index = 0
        frame_idx = 0
        
        # Sample every 5 frames for high speed
        sample_step = 5

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_step == 0:
                # Resize for fast comparison
                small = cv2.resize(frame, (160, 90))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                if prev_gray is not None:
                    diff = cv2.absdiff(gray, prev_gray)
                    mean_diff = float(diff.mean())

                    # Cut detected or time limit reached (> 15 seconds per scene)
                    frame_delta = frame_idx - scene_start_frame
                    if (mean_diff > threshold and frame_delta >= int(fps * 2.0)) or (frame_delta >= int(fps * 20.0)):
                        start_time = round(scene_start_frame / fps, 2)
                        end_time = round(frame_idx / fps, 2)
                        
                        # Save keyframe
                        keyframe_name = f"scene_{scene_index}_{int(start_time)}s.jpg"
                        keyframe_path = keyframe_dir / keyframe_name
                        cv2.imwrite(str(keyframe_path), frame)

                        scenes.append(SceneBoundary(
                            scene_index=scene_index,
                            start_time=start_time,
                            end_time=end_time,
                            keyframe_path=str(keyframe_path)
                        ))
                        scene_index += 1
                        scene_start_frame = frame_idx

                prev_gray = gray

            frame_idx += 1

        # Final scene
        if scene_start_frame < total_frames:
            start_time = round(scene_start_frame / fps, 2)
            end_time = round(duration, 2)
            keyframe_name = f"scene_{scene_index}_{int(start_time)}s.jpg"
            keyframe_path = keyframe_dir / keyframe_name
            if prev_gray is not None:
                # Get last frame keyframe
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 10))
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite(str(keyframe_path), frame)

            scenes.append(SceneBoundary(
                scene_index=scene_index,
                start_time=start_time,
                end_time=end_time,
                keyframe_path=str(keyframe_path) if keyframe_path.exists() else ""
            ))

        cap.release()
        return scenes if scenes else [SceneBoundary(scene_index=0, start_time=0.0, end_time=round(duration, 2))]


scene_detector = SceneDetectorService()
